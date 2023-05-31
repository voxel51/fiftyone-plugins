# check to see if the FIFTYONE_DIR is set otherwise print an error and exit
if [ -z "$FIFTYONE_DIR" ]; then
    echo "FIFTYONE_DIR is not set. Please set FIFTYONE_DIR to the directory where you cloned the FiftyOne repo"
    exit 1
fi

# check to see if yarn is installed
if ! command -v yarn &> /dev/null
then
    echo "yarn could not be found. Please install yarn before continuing"
    exit 1
fi

# check to see if yarn is at least version 3.x.x
if [ "$(yarn --version | cut -d. -f1)" -lt 3 ]; then
    echo "yarn version 3.x.x is required. Please upgrade yarn before continuing"
    exit 1
fi

echo "Installing dependencies with yarn..."

# if --link-only is not set run the yarn install command
if [ "$1" != "--link-only" ]; then
    yarn install
fi

yarn link $FIFTYONE_DIR/app --all --private --relative

echo "Adding tsconfig.fo.json files for plugins..."

node scripts/generate-tsconfig-fo.js
