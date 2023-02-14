const path = require('path')
const defaultResolutions = require('../../../package.json').resolutions

const {FIFTYONE_DIR} = process.env

module.exports.default = function fiftyoneRollup () {
	if (!FIFTYONE_DIR) {
		throw new Error(`FIFTYONE_DIR environment variable not set. This is required to resolve @fiftyone/* imports.`)
	}

  return {
		name: 'fiftyone-rollup',
		resolveId: {
			order: 'pre',
			async handler(source) {
				if (source.startsWith('@fiftyone')) {
          const pkg = source.split('/')[1]
          const modulePath = `${FIFTYONE_DIR}/app/packages/${pkg}`
					return this.resolve(modulePath, source, { skipSelf: true })
        }
				return null;
			}
		}
	};
}