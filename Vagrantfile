# -*- mode: ruby -*-
# vi: set ft=ruby :

unless Vagrant.has_plugin?("vagrant-vbguest")
  raise "Please install the vagrant-vbguest plugin by running `vagrant plugin install vagrant-vbguest`"
end

Vagrant.configure(2) do |config|
  config.vm.box = 'ubuntu/xenial64'
  config.vm.synced_folder '.', '/vagrant', disabled: true
  config.vm.synced_folder '.', '/home/vagrant/opencraft'

  config.vbguest.auto_update = true
  config.vbguest.auto_reboot = true

  config.vm.network 'forwarded_port', guest: 2001, host: 2001
  config.vm.network 'forwarded_port', guest: 5000, host: 5000
  config.vm.network 'forwarded_port', guest: 8888, host: 8888

  config.ssh.forward_x11 = true

  config.vm.provision "ansible" do |ansible|
    ansible.playbook = "deploy/playbooks/ocim-vagrant.yml"
    private_vars_file = "private.yml"
    if FileTest.exists?(private_vars_file)
      ansible.raw_arguments = ["--extra-vars", "@" + private_vars_file]
    end
  end

  config.vm.provider :virtualbox do |vb|
    vb.memory = 8096
    vb.cpus = 4

    # Allow DNS to work for Ubuntu host
    # http://askubuntu.com/questions/238040/how-do-i-fix-name-service-for-vagrant-client
    vb.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]
    vb.customize ["modifyvm", :id, "--natdnsproxy1", "on"]
    vb.customize ["modifyvm", :id, "--nictype1", "virtio"]
  end
end
