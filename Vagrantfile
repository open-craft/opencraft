# -*- mode: ruby -*-
# vi: set ft=ruby :

def install_plugins(plugins)
  not_installed = []
  plugins.each do |plugin|
    unless Vagrant.has_plugin?(plugin)
      not_installed << plugin
    end
  end

  unless not_installed.empty?
    puts "The following required plugins must be installed:"
    puts "'#{not_installed.join("', '")}'"
    print "Install? [y]/n: "
    unless STDIN.gets.chomp == "n"
      not_installed.each { |plugin| install_plugin(plugin) }
    else
      exit
    end
    $? ? continue : ( raise 'Plugin installation failed, see errors above.' )
  end
end

def install_plugin(plugin)
  system("vagrant plugin install #{plugin}")
end

# If plugins successfully installed, restart vagrant to detect changes.
def continue
  exec("vagrant #{ARGV[0]}")
end

required_plugins = ["vagrant-vbguest"]
install_plugins(required_plugins)

Vagrant.configure(2) do |config|
  # TODO: Switch back to the official box once it is released
  config.vm.box = 'opencraft/xenial64'
  config.vm.synced_folder '.', '/vagrant', disabled: true
  config.vm.synced_folder '.', '/home/vagrant/opencraft'

  config.vbguest.auto_update = true
  config.vbguest.auto_reboot = true

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
