import { readFileSync, readdirSync, statSync } from 'node:fs'
import { join } from 'node:path'

function files(dir) {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name)
    return statSync(path).isDirectory() ? files(path) : [path]
  })
}

const tsx = files('src').filter((path) => path.endsWith('.tsx'))
const missing = []
for (const path of tsx) {
  const text = readFileSync(path, 'utf8')
  const buttons = text.match(/<button[\s\S]*?>/g) || []
  for (const button of buttons) {
    for (const attr of ['data-qid=', 'data-qs-action=', 'title=']) {
      if (!button.includes(attr)) missing.push(`${path}: button missing ${attr}`)
    }
  }
}
if (missing.length) {
  console.error(missing.join('\n'))
  process.exit(1)
}
console.log(`OK: ${tsx.length} TSX files have required button qids`)
