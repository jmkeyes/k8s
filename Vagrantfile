# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  # Set up the hostmanager plugin for editing /etc/hosts.
  config.vagrant.plugins = ['vagrant-hostmanager']

  # Use the bento CentOS 7.x box.
  config.vm.box = 'bento/centos-7'

  # Provide some defaults for Virtualbox VMs.
  config.vm.provider :virtualbox do |vm|
    vm.linked_clone = true

    vm.cpus = 2
    vm.memory = 1024
    vm.default_nic_type = 'virtio'
  end

  # Ensure the hostmanager plugin is enabled.
  config.hostmanager.enabled = true
  config.hostmanager.manage_guest = true

  # Set up a Kubernetes master node.
  config.vm.define 'k8s-master-0' do |node|
    node.vm.hostname = 'k8s-master-0.example.com'
    node.vm.network :private_network, ip: '10.40.0.2'

    config.vm.network :forwarded_port, id: 'ssh', guest: 22, host: 2202
    config.vm.provider 'virtualbox' do |vm| vm.name = node.vm.hostname end
  end

  # Set up a Kubernetes worker node.
  config.vm.define 'k8s-worker-1' do |node|
    node.vm.hostname = 'k8s-worker-1.example.com'
    node.vm.network :private_network, ip: '10.40.0.10'

    config.vm.network :forwarded_port, id: 'ssh', guest: 22, host: 2210
    config.vm.provider 'virtualbox' do |vm| vm.name = node.vm.hostname end
  end
end
