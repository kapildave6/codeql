/**
 * @name id-token: write permission detected in GitHub Actions workflow
 * @description Detects when a workflow uses id-token: write permission, which allows the workflow to request OIDC tokens.
 * @kind problem
 * @problem.severity warning
 * @id github-actions/id-token-write
 * @tags security
 */

import semmle.code.yaml.AST

/**
 * Finds YAML files that are GitHub Actions workflow files.
 */
predicate isWorkflowFile(File f) {
  f.getRelativePath().matches("%.github/workflows/%.yml") or
  f.getRelativePath().matches("%.github/workflows/%.yaml")
}

from MappingEntry me, File f
where
  isWorkflowFile(f) and
  me.getFile() = f and
  me.getKey().getStringValue() = "id-token" and
  me.getValue().getStringValue() = "write"
select me, "Workflow uses 'id-token: write' permission which allows requesting OIDC tokens."

