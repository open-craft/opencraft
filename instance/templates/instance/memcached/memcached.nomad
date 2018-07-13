# Jobs need a globally consistent name, so we need to include the instance id.
job "memcached-1234" {
  datacenters = ["dc1"]
  type = "service"
  constraint {
    distinct_hosts = true
  }
  update {
    max_parallel = 1
  }
  migrate {
    max_parallel = 1
  }
  group "memcached" {
    count = 3    # Only 1 for stage
    task "memcached" {
      driver = "exec"
      config {
        command = "/usr/bin/memcached"
        args    = [
          # TCP port
          "-p", "${NOMAD_PORT_cache}",
          # Memory limit.  The daemon won't use more than the limit, but may use significantly less.
          "-m", "64", # MB
        ]
      }
      resources {
        cpu    = 25 # MHz
        # The daemon may grow bigger for some instances, capped at 64 MB, but will probably remain
        # smaller for most sandboxes and instances, so we don't want to make excessive allocations.
        memory = 32 # MB
        network {
          # Should be easily enough on average.  We don't want this to become a limiting factor for
          # scheduling.
          mbits = 1
          port "cache" {}
        }
      }
      # Register with Consul.
      service {
        name = "memcached-1234"
        tags = ["memcached"]
        port = "cache"
        check {
          name     = "alive"
          type     = "tcp"
          interval = "10s"
          timeout  = "1s"
        }
      }
    }
  }
}
