# terraform-modules

## Concept of this repository

Based on: https://cloudchronicles.blog/blog/GitHub-Powered-Terraform-Modules-Monorepo/
The idea is to create a pipeline that releases a module from the monorepo by copying its contents to root and tagging
it with a name and version.

## How to release a new version

The pipeline listens for a change in `module.json`, specifically the version set in it, and creates a tag for the module
if changed.

## How to use module in Terraform

Set the source of the module to this repository, setting the `ref` to the name and version of the desired module:

```
module "source_zip" {
  source = "git::https://github.com/Hermes-Supply-Chain/nl-terraform-modules?ref=source_zip/v1.0.0"
  (...)
}
```
