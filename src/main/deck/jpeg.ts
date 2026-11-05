export type JpegInfo = {
  width: number
  height: number
  baseline: boolean
  sampling: Array<[number, number]>
}

/** Read SOF0 (baseline) or SOF2 (progressive). Sampling factors are [H, V] per component. */
export function jpegInfo(buf: Buffer): JpegInfo {
  let i = 0
  while (i < buf.length - 1) {
    if (buf[i] !== 0xff) {
      i++
      continue
    }
    const marker = buf[i + 1]!
    if (marker === 0x00 || marker === 0xff) {
      i += 2
      continue
    }
    if (marker === 0xd8 || marker === 0xd9) {
      i += 2
      continue
    }
    if (i + 3 >= buf.length) break
    const len = buf.readUInt16BE(i + 2)
    if (marker === 0xc0 || marker === 0xc2) {
      const height = buf.readUInt16BE(i + 5)
      const width = buf.readUInt16BE(i + 7)
      const n = buf[i + 9]!
      const sampling: Array<[number, number]> = []
      let p = i + 10
      for (let c = 0; c < n; c++) {
        const samp = buf[p + 1]!
        sampling.push([samp >> 4, samp & 0x0f])
        p += 3
      }
      return { width, height, baseline: marker === 0xc0, sampling }
    }
    i += 2 + len
  }
  throw new Error('JPEG has no SOF marker')
}

export function is444(info: JpegInfo): boolean {
  return info.sampling.length > 0 && info.sampling.every(([h, v]) => h === 1 && v === 1)
}
