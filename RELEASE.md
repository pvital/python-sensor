# Release Steps

## PyPI

_Note: To release a new Instana package, you must be a project member of the [Instana package project on Pypi](https://pypi.org/project/instana/).
Contact [Peter Giacomo Lombardo](https://github.com/pglombardo) to be added._

1. Before releasing, assure that [tests have passed](https://circleci.com/gh/instana/workflows/python-sensor) and that the package has also been manually validated in various stacks.
2. `git checkout main && git pull --rebase && pip install -U twine`
3. Bump the package version in `instana/version.py`. `git` commit & push the version change to the `main` branch
4. Create a [draft Release on Github](https://github.com/instana/python-sensor/releases) using [./bin/create_general_release.py](https://github.com/instana/python-sensor/blob/main/bin/create_general_release.py)
5. Run `python setup.py sdist bdist_wheel` to create the packages file in `./dist/`
6. Upload the package to Pypi with twine: `twine upload dist/instana-<version>*`
7. Validate the new release on https://pypi.org/project/instana/
8. Update Python documentation with latest changes: https://docs.instana.io/ecosystem/python/
9. Publish the draft release on [Github](https://github.com/instana/python-sensor/releases)
10. Ensure that the new [Concourse CI resource version](
    https://ci.instana.io/teams/tracer-community/pipelines/tracer-test-suite:main/resources/instana-python-package)
    has been discovered. Trigger it manually if the automation doesn't do it. Also ensure that the [update job](
    https://ci.instana.io/teams/tracer-community/pipelines/tracer-test-suite%3Amain/jobs/update-python-package/)
    and its downstream jobs are successfull. In particular the `run-test-suite` doesn't report any errors.

## AWS Lambda Layer

To release a new AWS Lambda layer, see `bin/aws-lambda/lambda_build_publish_layer.py`.

```bash
./bin/aws-lambda/build_and_publish_lambda_layer.py [-dev|-prod]
./bin/create_lambda_release.py <version>
```

These scripts assume that you have the AWS CLI and Github CLI installed and credentials already configured.

Post release, remember to update documentation and the Instana UI.
