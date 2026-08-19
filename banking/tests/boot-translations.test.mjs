import assert from 'node:assert/strict'
import test from 'node:test'

import { resolveTranslationMessages } from '../src/lib/boot-translations.js'

test('waits for remote messages and lets them override boot messages', async () => {
  let release
  const remote = new Promise((resolve) => {
    release = resolve
  })
  const result = resolveTranslationMessages({ Banking: '银行' }, remote)
  const state = await Promise.race([result.then(() => 'rendered'), Promise.resolve('pending')])

  assert.equal(state, 'pending')
  release({ Beta: '测试版', Banking: '网上银行' })
  assert.deepEqual(await result, { Banking: '网上银行', Beta: '测试版' })
})

test('keeps boot messages when the remote catalog fails', async () => {
  const initial = { Banking: '银行' }
  assert.deepEqual(
    await resolveTranslationMessages(initial, Promise.reject(new Error('offline'))),
    initial,
  )
})
