import fs from 'fs'
import path from 'path'
import { demoAgents } from '../src/main/deck/demo'
import { renderUpright } from '../src/main/deck/render'

async function main(): Promise<void> {
  const dir = path.resolve('site/tiles')
  fs.mkdirSync(dir, { recursive: true })
  const agents = demoAgents()
  for (let i = 0; i < 6; i++) {
    const canvas = await renderUpright(agents[i]!, i + 1, false)
    fs.writeFileSync(path.join(dir, `key${i + 1}.png`), await canvas.encode('png'))
  }
  console.log('exported six tiles')
}

void main()
