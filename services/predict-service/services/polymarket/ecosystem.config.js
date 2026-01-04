/**
 * PM2 生态系统配置文件
 *
 * 功能：
 * - 自动重启（崩溃后立即重启）
 * - 内存限制（超过限制自动重启）
 * - 日志管理（自动轮换）
 * - 环境变量管理
 *
 * 使用方法：
 * - 启动: pm2 start ecosystem.config.js
 * - 停止: pm2 stop polymarket-bot
 * - 重启: pm2 restart polymarket-bot
 * - 日志: pm2 logs polymarket-bot
 * - 监控: pm2 monit
 * - 状态: pm2 status
 * - 开机自启: pm2 startup && pm2 save
 */

module.exports = {
    apps: [{
        // 应用名称
        name: 'polymarket-bot',

        // 启动脚本
        script: './src/bot.js',

        // 工作目录
        cwd: __dirname,

        // 实例数量（1 = 单进程，0 = CPU核心数）
        instances: 1,

        // 集群模式或fork模式
        exec_mode: 'fork',

        // 监听文件变化自动重启（开发环境）
        watch: false,

        // 忽略监听的文件/目录
        ignore_watch: [
            'node_modules',
            'data',
            'logs',
            '.git'
        ],

        // 最大内存限制（超过后自动重启）
        max_memory_restart: '2G',

        // 环境变量
        env: {
            NODE_ENV: 'production',
            NODE_OPTIONS: '--max-old-space-size=2048'
        },

        // 开发环境变量
        env_development: {
            NODE_ENV: 'development',
            NODE_OPTIONS: '--max-old-space-size=2048'
        },

        // 日志配置
        error_file: './logs/pm2-error.log',
        out_file: './logs/pm2-out.log',
        log_file: './logs/pm2-combined.log',

        // 日志时间格式
        time: true,

        // 日志轮换
        log_date_format: 'YYYY-MM-DD HH:mm:ss Z',

        // 合并日志
        merge_logs: true,

        // 自动重启配置
        autorestart: true,              // 崩溃后自动重启
        max_restarts: 10,               // 15分钟内最多重启10次
        min_uptime: '10s',              // 最小运行时间（低于此值认为启动失败）
        restart_delay: 4000,            // 重启延迟（毫秒）

        // 指数退避重启延迟（防止快速崩溃循环）
        exp_backoff_restart_delay: 100,

        // 崩溃自动重启前等待的最短时间
        listen_timeout: 10000,

        // 杀死进程前等待的时间
        kill_timeout: 5000,

        // 优雅关闭超时
        shutdown_with_message: true,
        wait_ready: false,

        // 进程ID文件
        pid_file: './data/polymarket-bot.pid',

        // 实例数量（用于集群模式）
        instance_var: 'INSTANCE_ID',

        // 崩溃后的action
        pmx: true,

        // 异常处理
        crash_restart: true,             // 异常崩溃后重启

        // 其他选项
        vizion: false,                   // 禁用版本控制元数据
        post_update: ['npm install'],    // 更新后执行的命令

        // cron重启（可选：每天凌晨3点重启）
        // cron_restart: '0 3 * * *',

        // Node.js参数
        node_args: [
            '--expose-gc',               // 暴露垃圾回收
            '--max-old-space-size=2048'  // 最大堆内存
        ]
    }]
};
