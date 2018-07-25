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
          # Log to stdout
          "-v",
          # Listen only on localhost
          "-l", "127.0.0.1",
          # TCP port
          "-p", "${NOMAD_PORT_cache}",
          # Memory limit.  The daemon won't use more than the limit, but may use significantly less.
          "-m", "64", # MB
        ]
      }
      resources {
        cpu    = 20 # MHz
        # The daemon may grow bigger for some instances, capped at 64 MB, but will probably remain
        # smaller for most sandboxes and instances, so we don't want to make excessive allocations.
        memory = 32 # MB
        disk = 0
        network {
          # Should be easily enough on average.  We don't want this to become a limiting factor for
          # scheduling.
          mbits = 1
          port "cache" {}
        }
      }
    }
    task "connect-proxy" {
      driver = "exec"
      config {
        command = "/usr/local/bin/consul"
        args    = [
          "connect", "proxy",
          "-service", "memcached-1234-${NOMAD_ALLOC_INDEX}",
          "-service-addr", "127.0.0.1:${NOMAD_PORT_memcached_cache}",
          "-listen", ":${NOMAD_PORT_cache}",
          "-register",
        ]
      }
      resources {
        cpu = 20 # MHz
        memory = 20 # MB
        disk = 0
        network {
          # Should be easily enough on average.  We don't want this to become a limiting factor for
          # scheduling.
          mbits = 1
          port "cache" {}
        }
      }
    }
  }
}
