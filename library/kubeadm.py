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
