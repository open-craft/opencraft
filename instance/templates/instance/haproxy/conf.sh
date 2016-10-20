{% autoescape off %}
set -e
flock -s {{ settings.LOAD_BALANCER_CONF_DIR }} cat > {{ conf_filename }} << EOF
{{ backend_conf }}
EOF
flock -s {{ settings.LOAD_BALANCER_BACKENDS_DIR }} cat > {{ backend_filename }} << EOF
{{ backend_map }}
EOF
{% endautoescape %}
