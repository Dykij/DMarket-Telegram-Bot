/**
 * PM2 Ecosystem Configuration for DMarket Telegram Bot
 *
 * Production-grade process management with clustering, monitoring, and auto-restart.
 *
 * Usage:
 *   pm2 start ecosystem.config.js --env production
 *   pm2 start ecosystem.config.js --env development
 *   pm2 reload ecosystem.config.js  # Zero-downtime reload
 *   pm2 logs dmarket-bot           # View logs
 *   pm2 monit                      # Monitor resources
 */

module.exports = {
  apps: [
    {
      // Application settings
      name: 'dmarket-bot',
      script: 'python',
      args: '-m src',
      cwd: './',
      interpreter: 'none',  // Don't use Node interpreter for Python

      // Clustering and scaling
      instances: 1,  // Python bot is single-threaded, use 1 instance
      exec_mode: 'fork',  // 'cluster' mode only for Node.js

      // Auto-restart configuration
      autorestart: true,
      watch: false,  // Disable in production (enable in dev if needed)
      max_memory_restart: '500M',  // Restart if memory exceeds 500MB
      min_uptime: '10s',  // Min uptime before considering started
      max_restarts: 10,  // Max restarts within restart_delay window
      restart_delay: 5000,  // Delay between restarts (5 seconds)

      // Logging
      error_file: 'logs/pm2-error.log',
      out_file: 'logs/pm2-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      merge_logs: true,
      log_type: 'json',  // JSON logs for better parsing

      // Environment variables
      env: {
        NODE_ENV: 'development',
        LOG_LEVEL: 'DEBUG',
        PYTHONUNBUFFERED: '1',
      },

      env_production: {
        NODE_ENV: 'production',
        LOG_LEVEL: 'INFO',
        PYTHONUNBUFFERED: '1',
      },

      // Health monitoring
      listen_timeout: 10000,  // Timeout for app to be ready (10s)
      kill_timeout: 5000,  // Timeout for graceful shutdown (5s)

      // Graceful shutdown
      shutdown_with_message: true,
      wait_ready: false,  // Python bot doesn't send ready signal

      // Error handling
      ignore_watch: [
        'node_modules',
        'logs',
        'data',
        '.git',
        '.venv',
      ],

      // Performance monitoring (PM2 Plus integration)
      pmx: true,

      // Advanced configuration
      vizion: false,  // Disable git metadata collection
      post_update: ['echo "App updated"'],  // Run after update

      // Cron restart (optional, useful for memory cleanup)
      cron_restart: '0 3 * * *',  // Restart daily at 3 AM (optional, comment out if not needed)
    },
  ],

  // Deploy configuration (optional, for PM2 deploy feature)
  deploy: {
    production: {
      user: 'deploy',
      host: ['your-server-ip'],
      ref: 'origin/main',
      repo: 'https://github.com/your-username/dmarket-telegram-bot.git',
      path: '/var/www/dmarket-bot',
      'post-deploy': 'pip install -r requirements.txt && pm2 reload ecosystem.config.js --env production',
      'pre-deploy-local': 'echo "Deploying to production..."',
      'post-setup': 'echo "Setup complete"',
    },

    staging: {
      user: 'deploy',
      host: ['staging-server-ip'],
      ref: 'origin/develop',
      repo: 'https://github.com/your-username/dmarket-telegram-bot.git',
      path: '/var/www/dmarket-bot-staging',
      'post-deploy': 'pip install -r requirements.txt && pm2 reload ecosystem.config.js --env development',
    },
  },
};
