module.exports = {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'type-enum': [2, 'always', ['feat','fix','refactor','docs','chore','perf','test']],
    'subject-min-length': [2, 'always', 12], // 备注最少12个字，杜绝简短模糊提交
  }
}
