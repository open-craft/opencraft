# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure(2) do |config|
  # TODO: Switch back to the official box once it is released
  config.vm.box = 'opencraft/xenial64'
  config.vm.box_url = 'http://opencraft.com/files/vagrant-opencraft-xenial64.box'
  config.vm.synced_folder '.', '/vagrant', disabled: true
  config.vm.synced_folder '.', '/home/vagrant/opencraft'

  config.vm.network 'forwarded_port', guest: 2001, host: 2001
  config.vm.network 'forwarded_port', guest: 5000, host: 5000
  config.vm.network 'forwarded_port', guest: 8888, host: 8888

  config.ssh.forward_x11 = true

  config.vm.provision 'shell',
                      path: 'bin/bootstrap',
                      privileged: false,
                      keep_color: true

  config.vm.provider :virtualbox do |vb|
    vb.memory = 1024
    # Allow DNS to work for Ubuntu host
    # http://askubuntu.com/questions/238040/how-do-i-fix-name-service-for-vagrant-client
    vb.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]
  end
end
