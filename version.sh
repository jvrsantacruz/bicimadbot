set -e

function confirm () {
    read -r -p "Are you sure? [y/N]: " response
    [[ $response =~ [Yy]$ ]]
}

python upversion.py up $@
dicto view --prepend HISTORY.rst
git diff
VERSION=$(python setup.py --version | tr -d '\n')
echo "Bumping $VERSION"
confirm && git commit -am "Bumps version ${VERSION}" && git tag ${VERSION}
