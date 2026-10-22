import assert from "node:assert/strict"
import { readdirSync, readFileSync } from "node:fs"
import { join } from "node:path"
import test from "node:test"
import { fileURLToPath } from "node:url"
import ts from "typescript"

import { extractTranslationKeys } from "../scripts/extract-translation-keys.mjs"

const sourceRoot = fileURLToPath(new URL("../src/", import.meta.url))
const keyboardLabels = new Set(["B", "Ctrl", "G", "I", "P", "R", "S", "Z"])
const technicalExamples = new Set(["transaction_amount * 0.25"])
const visibleProperties = new Set([
  "aria-label",
  "description",
  "emptyText",
  "helperText",
  "label",
  "message",
  "placeholder",
  "text",
  "title",
])

function sourceFiles(directory) {
  return readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const path = join(directory, entry.name)
    if (entry.isDirectory()) return sourceFiles(path)
    return path.endsWith(".tsx") ? [path] : []
  })
}

function untranslatedStaticCopy(node) {
  if (ts.isCallExpression(node) && ts.isIdentifier(node.expression) && node.expression.text === "_") {
    return []
  }
  if (ts.isStringLiteralLike(node)) {
    return /[A-Za-z]/.test(node.text) ? [node.text] : []
  }
  if (ts.isTemplateExpression(node)) {
    return [node.head.text, ...node.templateSpans.flatMap((span) => [
      ...untranslatedStaticCopy(span.expression),
      span.literal.text,
    ])].filter((text) => /[A-Za-z]/.test(text))
  }
  if (ts.isConditionalExpression(node)) {
    return [
      ...untranslatedStaticCopy(node.whenTrue),
      ...untranslatedStaticCopy(node.whenFalse),
    ]
  }

  const untranslated = []
  ts.forEachChild(node, (child) => untranslated.push(...untranslatedStaticCopy(child)))
  return untranslated
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
      if (ts.isJsxAttribute(node) && visibleProperties.has(node.name.text)) {
        const initializer = node.initializer
        const expression =
          initializer && ts.isJsxExpression(initializer) ? initializer.expression : initializer
        const text = expression?.getText(source) ?? ""
        const isCurrencyPlaceholder = /currencySymbol|decimalSeparator/.test(text)
        const staticCopy = expression ? untranslatedStaticCopy(expression) : []

        if (staticCopy.length && !isCurrencyPlaceholder) {
          const { line } = source.getLineAndCharacterOfPosition(node.getStart(source))
          untranslated.push(`${path}:${line + 1}: ${staticCopy.join(" | ")}`)
        }
      }
      ts.forEachChild(node, visit)
    }

    visit(source)
  }

  assert.deepEqual(untranslated, [])
})

test("translation key inventory matches the TypeScript source", () => {
  const inventory = JSON.parse(
    readFileSync(fileURLToPath(new URL("../translation-keys.json", import.meta.url)), "utf8"),
  )
  assert.deepEqual(inventory, extractTranslationKeys(sourceRoot))
})
