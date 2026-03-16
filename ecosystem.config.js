module.exports = {
  apps: [
    {
      name: "safebite-backend",
      script: "/opt/safebite/backend/venv/bin/uvicorn",
      args: "main:app --host 127.0.0.1 --port 8000 --workers 2",
      cwd: "/opt/safebite/backend",
      interpreter: "none",
      autorestart: true,
      watch: false,
      max_restarts: 10,
      restart_delay: 3000,
      out_file: "/opt/safebite/logs/backend-out.log",
      error_file: "/opt/safebite/logs/backend-error.log"
    },
    {
      name: "safebite-frontend",
      script: "python3",
      args: "-m http.server 3000",
      cwd: "/opt/safebite/frontend/out",
      interpreter: "none",
      autorestart: true,
      watch: false,
      max_restarts: 10,
      restart_delay: 3000,
      out_file: "/opt/safebite/logs/frontend-out.log",
      error_file: "/opt/safebite/logs/frontend-error.log"
    },
    {
      name: "safebite-caddy",
      script: "/usr/local/bin/caddy",
      args: "run --config /opt/safebite/caddy/Caddyfile --adapter caddyfile",
      cwd: "/opt/safebite/caddy",
      interpreter: "none",
      env: {
        HOME: "/root",
        XDG_DATA_HOME: "/opt/safebite/caddy/data",
        XDG_CONFIG_HOME: "/opt/safebite/caddy/config"
      },
      autorestart: true,
      watch: false,
      max_restarts: 10,
      restart_delay: 3000,
      out_file: "/opt/safebite/logs/caddy-out.log",
      error_file: "/opt/safebite/logs/caddy-error.log"
    },
    {
      name: "safebite-webhook",
      script: "/opt/safebite/webhook_server.py",
      interpreter: "python3",
      autorestart: true,
      watch: false,
      max_restarts: 10,
      restart_delay: 3000,
      out_file: "/opt/safebite/logs/webhook-out.log",
      error_file: "/opt/safebite/logs/webhook-error.log"
    }
  ]
};
