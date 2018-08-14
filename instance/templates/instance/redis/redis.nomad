# Jobs need a globally consistent name, so we need to include the instance id.
job "redis-1234" {
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
  group "redis" {
    count = 1
    task "server" {
      driver = "exec"
      config {
        command = "/usr/bin/redis-server"
        args    = [
          # Listen only on localhost
          "--bind", "127.0.0.1",
          # TCP port
          "--port", "${NOMAD_PORT_redis}",
        ]
      }
      resources {
        cpu    = 20 # MHz
        # The daemon may in theory grow bigger than this, but given that it only stores the Celery
        # queue it will in general be much smaller.
        memory = 32 # MB
        disk = 0
        network {
          # Should be easily enough on average.  We don't want this to become a limiting factor for
          # scheduling.
          mbits = 1
          port "redis" {}
        }
      }
    }
    task "connect-proxy" {
      driver = "exec"
      config {
        command = "/usr/local/bin/consul"
        args    = [
          "connect", "proxy",
          "-service", "redis-1234",
          "-service-addr", "127.0.0.1:${NOMAD_PORT_server_redis}",
          "-listen", ":${NOMAD_PORT_redis}",
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
          port "redis" {}
        }
      }
    }
  }
}
