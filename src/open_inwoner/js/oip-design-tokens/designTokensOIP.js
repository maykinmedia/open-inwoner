// designTokens.js
const designTokens = {
  colors: {
    oiColor: 'red',
  },
}

function generateCSS() {
  let css = ':root {\n'

  for (const category in designTokens) {
    const tokens = designTokens[category]

    for (const token in tokens) {
      css += `  --${token}: ${tokens[token]};\n`
    }
  }

  css += '}\n'

  return css
}

module.exports = generateCSS
