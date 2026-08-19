import assert from "node:assert/strict"
import { readdirSync, readFileSync } from "node:fs"
import { join } from "node:path"
import test from "node:test"
import { fileURLToPath } from "node:url"
import ts from "typescript"

const sourceRoot = fileURLToPath(new URL("../src/", import.meta.url))
const keyboardLabels = new Set(["B", "Ctrl", "G", "I", "P", "R", "S", "Z"])
const technicalExamples = new Set(["transaction_amount * 0.25"])

function sourceFiles(directory) {
  return readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const path = join(directory, entry.name)
    if (entry.isDirectory()) return sourceFiles(path)
    return path.endsWith(".tsx") ? [path] : []
  })
}

test("visible banking copy goes through the translation helper", () => {
  const untranslated = []

  for (const path of sourceFiles(sourceRoot)) {
    const source = ts.createSourceFile(
      path,
      readFileSync(path, "utf8"),
      ts.ScriptTarget.Latest,
      true,
      ts.ScriptKind.TSX,
    )

    function visit(node) {
      if (ts.isJsxText(node)) {
        const text = node.getText(source).replace(/\s+/g, " ").trim()
        const isEntity = /^(?:&[a-z]+;)+$/.test(text)
        if (
          /[A-Za-z]/.test(text) &&
          !keyboardLabels.has(text) &&
          !technicalExamples.has(text) &&
          !isEntity
        ) {
          const { line } = source.getLineAndCharacterOfPosition(node.getStart(source))
          untranslated.push(`${path}:${line + 1}: ${text}`)
        }
      }
      ts.forEachChild(node, visit)
    }

    visit(source)
  }

  assert.deepEqual(untranslated, [])
})
