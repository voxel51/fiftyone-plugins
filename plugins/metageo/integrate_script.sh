#!/bin/bash

echo "🔧 Integrating Step Components into MetageoView.tsx"
echo "=================================================="

# Check if the file exists
if [ ! -f "src/MetageoView.tsx" ]; then
    echo "❌ Error: src/MetageoView.tsx not found!"
    exit 1
fi

echo "✅ Found MetageoView.tsx"

# Check if step components exist
if [ ! -f "src/steps/IndexConfigurationStep.tsx" ]; then
    echo "❌ Error: IndexConfigurationStep.tsx not found!"
    exit 1
fi

if [ ! -f "src/steps/IndexingStep.tsx" ]; then
    echo "❌ Error: IndexingStep.tsx not found!"
    exit 1
fi

if [ ! -f "src/steps/MappingStep.tsx" ]; then
    echo "❌ Error: MappingStep.tsx not found!"
    exit 1
fi

echo "✅ All step components found"

echo ""
echo "📋 Manual Integration Required:"
echo "================================"
echo ""
echo "1. Add these imports at the top of MetageoView.tsx:"
echo "   import IndexConfigurationStep from './steps/IndexConfigurationStep';"
echo "   import IndexingStep from './steps/IndexingStep';"
echo "   import MappingStep from './steps/MappingStep';"
echo ""
echo "2. Replace Step 0 content with:"
echo "   {activeStep === 0 && ("
echo "     <IndexConfigurationStep"
echo "       stepData={stepData}"
echo "       setStepData={setStepData}"
echo "       loading={loading}"
echo "       sampleDistributionLoading={sampleDistributionLoading}"
echo "       realSampleDistribution={realSampleDistribution}"
echo "       quadtreeCells={quadtreeCells}"
echo "       hasExistingIndex={hasExistingIndex}"
echo "       existingIndexData={existingIndexData}"
echo "       onAutoBbox={handleAutoBbox}"
echo "       onCalculateSampleDistribution={handleCalculateSampleDistribution}"
echo "       onStartIndexing={handleStartIndexing}"
echo "       onPauseIndexing={handlePauseIndexing}"
echo "       onRetryIndexing={handleRetryIndexing}"
echo "       onCancelIndexing={handleCancelIndexing}"
echo "       onDropIndex={handleDropIndex}"
echo "       onQuadtreeCellsChange={setQuadtreeCells}"
echo "       geoFields={data?.geo_fields || []}"
echo "     />"
echo "   )}"
echo ""
echo "3. Replace Step 1 content with:"
echo "   {activeStep === 1 && ("
echo "     <IndexingStep"
echo "       stepData={stepData}"
echo "     />"
echo "   )}"
echo ""
echo "4. Replace Step 2 content with:"
echo "   {activeStep === 2 && ("
echo "     <MappingStep"
echo "       stepData={stepData}"
echo "       setStepData={setStepData}"
echo "       osmTags={osmTags}"
echo "       osmTagsLoading={osmTagsLoading}"
echo "       onLoadOsmTags={handleLoadOsmTags}"
echo "     />"
echo "   )}"
echo ""
echo "5. Build the project:"
echo "   yarn build"
echo ""
echo "🎯 The components are ready to use!"
echo "📁 Check the integrate_steps.md file for detailed instructions."
