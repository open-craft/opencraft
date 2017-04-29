class Resource(models.Model):
    client = ForeignKey(Client)
    owned_by = ForgeignKey(Resource, null=True)
    name = CharField(blank=False, max_length=128)
    configuration = JSONField(null=False)
    types = ResourceTypeRegistry()
    owned_resources = ResourceManger()

    @property
    def configuration_schema(self):
        """ Define the options used to configure this resource. """
        return {}  # No configurable options by default

    @property
    def state(self):
        """
        The current state of this resource.
        The return value is always a subclass of ResourceState, and typically will be a subclass of:
          NeedsRefreshState, ApplyingConfigurationState, NeedsInputState, ReadyState, ErrorState, or DestroyingState
        Each state supports common methods like get_status_message(), get_status_color(), allow_configuration_changes()
        """
        return self._state

    def build_form():
        """ Convert self.configuration_schema into a Django form """
        pass


class VmProvider(Resource):
    """ A provider that can provision virtual machines """
    class Meta:
        proxy = True

    def get_flavors(self):
        """ Get available VM sizes """
        raise NotImplementedError
    def list_instances(self):
        """ List instances currently provisioned on this account. """
        raise NotImplementedError
    def provision_vm(self, flavor, image):
        """ Start the process of provisioning a new VM. Returns a VmInstance """
        raise NotImplementedError


class OpenStackVmProvider(VmProvider):
    # Implementation here.


class VmInstance(Resource):
    """
    A virtual machine.
    configuration options: flavor, image, is_powered_on
    """
    class Meta:
        proxy = True


class OpenStackVmInstance(VmInstance):
    # Implementation here


class OpenEdxSandboxInstance(Resource):
    """
    A single-server installation of Open edX.
    Useful for development, QA, demos, etc.
    """
    class Meta:
        proxy = True

    @property
    def configuration_schema(self):
        return ResourceConfiguration(
            platform_repo=Option(
                type=str,
                required=True,
                default="https://github.com/edx/edx-platform.git",
            ),
            platform_commit=Option(
                type=str,
                required=True,
                default="master",
            ),
            vm_provider=Option(
                type=Resource.types.VmProvider,
                required=True,
            ),
            vm_flavor=Option(
                type=str,
                required=True,
            ),
            mysql_server=Option(
                type=Resource.types.MysqlServer,
                null=True,
                default=None,
                description="Leave blank to use an ephemeral MySQl server on the sandbox VM.",
            ),
            mongo_server=Option(
                type=Resource.types.MongodbServer,
                null=True,
                default=None,
                description="Leave blank to use an ephemeral MongoDB server on the sandbox VM.",
            ),
            ansible_vars=Option(
                type=str,
                default="",
            ),
        )

    class ApplyingConfigurationState(ApplyingConfigurationState):
        # self.conf accesses the Resource's current 'configuration' data
        # self.owned_resources accesses the Resource's list of owned resources
        def enter_state(self):
            if self.conf.vm_provider.changed:
                if self.owned_resources["vm"]:
                    # Free the old VM (code will set its owner to none and queue deprovisioning)
                    del self.owned_resources["vm"]
                # First things first: Provision a virtual machine for use.
                self.owned_resources["vm"] = self.conf.vm_provider.provision_vm(flavor=self.conf.vm_flavor, image="ubuntu12.04.5")
            elif self.conf.vm_flavor.changed:
                self.owned_resources["vm"].configure(flavor=self.conf.vm_flavor)
                self.resource.update_owned_resources()  # Iterate child resources and move any that are in NeedsRefreshState to ApplyingConfigurationState
            elif self.conf.platform_repo.changed or self.conf.platform_commit.changed:
                # Configuration has changed. Run ansible again.
                self._configure_ansible()
                self.resource.update_owned_resources()  # Iterate child resources and move any that are in NeedsRefreshState to ApplyingConfigurationState
            super().enter_state()

        def handle_signal(self, signal):
            if signal.sender == self.owned_resources["vm"] and isinstance(signal, VmInstance.StateChanged):
                if isinstance(signal.new_state, ReadyState):
                    # The VM is ready, now use ansible to install/update its software and configuration
                    self._configure_ansible()
                    self.resource.update_owned_resources()  # Iterate child resources and move any that are in NeedsRefreshState to ApplyingConfigurationState
                else:
                    self.push_state(ErrorState, description="VM provisioning failed.", link_resource=self.res["vm"])
            super().handle_signal(signal)  # This contains logic that will change this resource to a ReadyState once all child resources are in ReadyStates

        def _configure_ansible(self):
            if not self.owned_resources["ansibler"]:
                self.owned_resources["ansibler"] = self.resource.create_owned_resource(AnsibleProvisioner)
            self.owned_resources["ansibler"].configure(
                vm=self.owned_resources["vm"],
                platform_repo=self.conf.platform_repo,
                platform_commit=self.conf.platform_commit,
                vars=self.conf.ansible_vars,
            )
