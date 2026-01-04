/**
 * i18n 语言包加载器
 */
const zhCN = require('./zh-CN');
const en = require('./en');

const packs = { 'zh-CN': zhCN, 'en': en };
const VALID_LANGS = ['zh-CN', 'en'];

/**
 * 获取语言包
 * @param {string} lang - 语言代码 'zh-CN' | 'en'
 */
function t(lang = 'zh-CN') {
  const validLang = VALID_LANGS.includes(lang) ? lang : 'zh-CN';
  return packs[validLang];
}

module.exports = { t, packs, VALID_LANGS };
