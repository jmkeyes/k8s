#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import yaml

from ansible.module_utils.basic import AnsibleModule

class KubeAdm(object):
    STATES = ['initialized', 'joined', 'reset']

    def __init__(self, module):
        self.module = module
        self.kubeadm = module.get_bin_path('kubeadm', True)

    def _kubeadm(self, arguments):
        command = [self.kubeadm] + list(arguments)
        return self.module.run_command(command)

    # 'kubeadm version -o short' -> "v1.14.0"
    def version(self):
        command = ['version', '-o', 'short']
        output = self._kubeadm(command)[1]
        return output.splitlines()[0]

    def _init_preflight_checks(self, ignore=[]):
        command = ['init', 'phase', 'preflight']

        # If we had to ignore some checks, inject them.
        if len(ignore) > 0:
            flag = '--ignore-preflight-checks={}'.format(','.join(ignore))
            command.append(flag)

        # Actually execute the preflight check(s) and return stderr.
        _, _, err = self._kubeadm(command)

        # Compile a regexp to match warnings and errors.
        pattern = re.compile('^\\t\[(WARNING|ERROR) (\w+)]: (.*)$')

        # Try to match the regex against the input lines.
        candidates = [pattern.match(line) for line in err.splitlines()]

        # Get a list of 3-tuples for each matched candidate.
        matches = [m.group(1, 2, 3) for m in candidates if m != None]

        # Extract all warnings from the list of matches.
        warnings = filter(lambda m: m[0] == 'WARNING', matches)

        # Extract all errors from the list of matches.
        errors = filter(lambda m: m[0] == 'ERROR', matches)

        # Extract the useful parts of the matches.
        useful = lambda m: "({}) {}".format(m[1], m[2])

        # Return them to the caller.
        return map(useful, warnings), map(useful, errors)

    def _get_init_configuration(self):
        output = None

        # If it's on disk, load it. XXX: Potential race condition.
        if os.path.exists('/etc/kubernetes/kubeadm.init.yaml'):
            with open('/etc/kubernetes/kubeadm.init.yaml') as config:
                output = yaml.safe_load(config.read())
        else:
            # If it's not on disk, use the default.
            command = ['config', 'print', 'init-defaults']
            output = self._kubeadm(command)[1]

        return yaml.safe_load_all(output)

    def init(self):
        # kubeadm init phase preflight [--ignore-preflight-checks=A,B,C]
        # XXX: This also pulls in docker images; repository can only be overridden by YAML.
        warnings, errors = self._init_preflight_checks()

        # Display any warnings shown from preflight checks
        for warning in warnings:
            self.module.warn(warning)

        # Fail the module immediately if there are errors.
        if len(errors) > 0:
            self.module.fail_json(msg='kubeadm failed preflight checks', errors=errors)

        init_config, cluster_config = self._get_init_configuration()

        self.module.warn('InitConfiguration:\n{}'.format(init_config))
        self.module.warn('ClusterConfiguration:\n{}'.format(init_config))

        return dict()

    def _get_default_join_config(self):
        command = ['config', 'print', 'join-defaults']
        output = self._kubeadm(command)[1]
        return yaml.safe_load_all(output)

    def join(self):
        join_config = self._get_join_configuration()

        self.module.warn('JoinConfiguration:\n{}'.format(join_config))

        return dict()

    def reset(self):
        command = ['reset', '--force']
        rc, stdout, stderr = self._kubeadm(command)
        return dict(rc=rc, stdout=stdout, stderr=stderr)

def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(type='str', required=True, choices=KubeAdm.STATES),
            bootstrap_token=dict(type='str'),
        ),
    )

    kubeadm = KubeAdm(module)

    state = module.params.get('state')

    if state not in KubeAdm.STATES:
        module.fail_json(msg='Unrecognized state "%s"' % state)

    result = dict()

    if state == 'initialized':
        result.update(kubeadm.init())

    if state == 'joined':
        result.update(kubeadm.join())

    if state == 'reset':
        result.update(kubeadm.reset())

    module.exit_json(**result)

if __name__ == '__main__':
    main()
