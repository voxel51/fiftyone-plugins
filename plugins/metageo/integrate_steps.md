# Integrating Step Components into MetageoView.tsx

## Overview
The step components have been created and need to be integrated into the main MetageoView.tsx file.

## Steps to Integrate

### 1. Import the Components
Add these imports at the top of MetageoView.tsx:

```tsx
import IndexConfigurationStep from "./steps/IndexConfigurationStep";
import IndexingStep from "./steps/IndexingStep";
import MappingStep from "./steps/MappingStep";
```

### 2. Replace Step 0 Content
Find the section `{activeStep === 0 && (` and replace the entire content with:

```tsx
{activeStep === 0 && (
  <IndexConfigurationStep
    stepData={stepData}
    setStepData={setStepData}
    loading={loading}
    sampleDistributionLoading={sampleDistributionLoading}
    realSampleDistribution={realSampleDistribution}
    quadtreeCells={quadtreeCells}
    hasExistingIndex={hasExistingIndex}
    existingIndexData={existingIndexData}
    onAutoBbox={handleAutoBbox}
    onCalculateSampleDistribution={handleCalculateSampleDistribution}
    onStartIndexing={handleStartIndexing}
    onPauseIndexing={handlePauseIndexing}
    onRetryIndexing={handleRetryIndexing}
    onCancelIndexing={handleCancelIndexing}
    onDropIndex={handleDropIndex}
    onQuadtreeCellsChange={setQuadtreeCells}
    geoFields={data?.geo_fields || []}
  />
)}
```

### 3. Replace Step 1 Content
Find the section `{activeStep === 1 && (` and replace with:

```tsx
{activeStep === 1 && (
  <IndexingStep
    stepData={stepData}
  />
)}
```

### 4. Replace Step 2 Content
Find the section `{activeStep === 2 && (` and replace with:

```tsx
{activeStep === 2 && (
  <MappingStep
    stepData={stepData}
    setStepData={setStepData}
    osmTags={osmTags}
    osmTagsLoading={osmTagsLoading}
    onLoadOsmTags={handleLoadOsmTags}
  />
)}
```

## Benefits
- Cleaner, more maintainable code
- Each step is now a separate component
- Easier to test and modify individual steps
- Better separation of concerns

## Notes
- Make sure all required props are passed correctly
- The components handle their own internal state
- The main file still manages the overall step flow
