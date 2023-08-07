import { registerComponent, PluginComponentType } from "@fiftyone/plugins";
import { useOperatorExecutor } from "@fiftyone/operators";
import { useState } from "react";
import { useRecoilValue } from "recoil";
import * as fos from "@fiftyone/state";
import { Box, Slider, Button, TextField, Stack, Typography, Select, MenuItem, FormControl, InputLabel } from "@mui/material";


export default function InterpolationPanel() {
  const [sliderValue, setSliderValue] = useState(0)
  const [leftExtremeValue, setLeftExtremeValue] = useState('')
  const [rightExtremeValue, setRightExtremeValue] = useState('')
  const validBrainRuns = getValidBrainRuns();
  const [brainRunValue, setBrainRunValue] = useState(validBrainRuns[0]);

  const handleLeftChange = (event) => {
    setLeftExtremeValue(event.target.value);
  };

  const handleRightChange = (event) => {
    setRightExtremeValue(event.target.value);
  };

  const handleBrainRunChange = (event) => {
    setBrainRunValue(event.target.value)
  };

  const operatorExecutor = useOperatorExecutor('@voxel51/interpolation/interpolator')

  return (
    <Box p={4}>
      <Box sx={{ display: 'flex', justifyContent: 'left' }}>
      <FormControl>
        <InputLabel id="my-select-label">My Label</InputLabel>
        <Select
            labelId="demo-simple-select-label"
            id="demo-simple-select"
            value={brainRunValue}
            label="Brain Key"
            onChange={handleBrainRunChange}
          >
            
          {validBrainRuns.map((item) => (
            <MenuItem key={item} value={item}>
              {item}
            </MenuItem>
          ))}
          </Select>
          </FormControl>
        </Box>


      <Stack direction="column" spacing={2}>
      <Box sx={{ display: 'flex', justifyContent: 'center' }}>
          <Typography id="input-slider">
             
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', justifyContent: 'center' }}>
          <Typography id="input-slider">
            Weight
          </Typography>
        </Box>
        <Stack direction="row" spacing={2}>
          <TextField 
            id="outlined-basic" 
            label="Left Prompt" 
            variant="outlined"
            value={leftExtremeValue}
            onChange={handleLeftChange}
            />
          <Slider 
            min={0}
            max={1}
            defaultValue={0.5}
            step={0.01}
            track={false}
            onChange={(e, value) => {
              console.log("value", value);
              setSliderValue(value)
            }}
          />
          <TextField 
            id="outlined-basic" 
            label="Right Prompt" 
            variant="outlined" 
            value={rightExtremeValue}
            onChange={handleRightChange}
            />
        </Stack>
        <Box sx={{ display: 'flex', justifyContent: 'center' }}>
          <Button variant="contained"
          onClick={() => {
            operatorExecutor.execute({ 
              "left_extreme": leftExtremeValue,
              "right_extreme": rightExtremeValue,
              "slider_value": sliderValue,
              "index": brainRunValue
             })
          }}
          >
          Execute operator
        </Button>
        </Box>

      </Stack>
      
    </Box>

    
  )
}


const InterpolationIcon = ({ size = 41, style = {} }) => {
  return (
    <svg version="1.0" style={style} xmlns="http://www.w3.org/2000/svg" stroke-width="1.5" width={size} height={size} viewBox="0 0 481.000000 494.000000" preserveAspectRatio="xMidYMid meet" class="h-6 w-6" role="img">
      <g transform="translate(0.000000,494.000000) scale(0.100000,-0.100000)" fill="#ffffff" stroke="none">
        <path d="M4534 4600 c-37 -15 -64 -59 -64 -106 0 -92 107 -139 179 -78 95 80 1 231 -115 184z"/>
        <path d="M3745 4574 c-16 -2 -73 -9 -125 -15 -297 -33 -570 -131 -758 -271 l-82 -61 21 -23 20 -22 72 54 c178 134 420 223 727 266 104 14 633 19 731 6 l57 -8 4 29 c4 26 1 30 -26 35 -38 7 -599 16 -641 10z"/>
        <path d="M2628 4173 c-33 -21 -48 -53 -48 -101 1 -111 153 -142 205 -42 19 37 19 63 0 100 -29 55 -104 76 -157 43z"/>
        <path d="M2552 3913 c-53 -102 -86 -261 -106 -498 -20 -230 -24 -263 -43 -360 -17 -89 -62 -219 -93 -273 -12 -19 -20 -35 -18 -36 2 -1 13 -9 25 -20 22 -18 22 -18 54 46 75 149 101 266 129 583 23 261 40 360 84 477 24 62 30 90 22 96 -30 23 -36 21 -54 -15z"/>
        <path d="M2144 2666 c-28 -28 -34 -41 -34 -77 1 -68 44 -109 114 -109 104 0 142 146 52 201 -49 30 -92 25 -132 -15z"/>
        <path d="M2005 2454 c-195 -137 -434 -197 -950 -239 -239 -20 -373 -39 -481 -71 -82 -23 -178 -66 -219 -98 -20 -15 -20 -15 1 -36 l21 -21 49 31 c110 69 283 106 634 135 537 44 767 104 993 257 56 38 58 40 41 59 -23 25 -30 24 -89 -17z"/>
        <path d="M177 1967 c-60 -48 -54 -135 13 -180 83 -57 199 40 160 133 -29 69 -116 93 -173 47z"/>
        <path d="M144 1683 c-11 -75 3 -230 32 -343 51 -203 156 -433 322 -711 125 -206 115 -194 145 -174 l25 16 -86 137 c-48 75 -127 218 -177 317 -143 283 -210 512 -203 698 2 69 0 90 -12 97 -28 18 -39 10 -46 -37z"/>
        <path d="M659 391 c-55 -55 -33 -150 41 -181 70 -29 150 29 150 109 0 24 -9 42 -34 67 -29 29 -41 34 -81 34 -38 0 -52 -5 -76 -29z"/>
      </g>
    </svg>
  )
}


registerComponent({
  name: 'InterpolationPanel',
  label: 'Interpolation',
  component: InterpolationPanel,
  type: PluginComponentType.Panel,
  activator: interpolationActivator,
  Icon: () => <InterpolationIcon size={"1rem"} style={{ marginRight: "0.5rem" }} />,
})


function getValidBrainRuns() {
  const dataset = useRecoilValue(fos.dataset);
  const brainMethods = dataset.brainMethods;
  const validBrainRuns = [];
  for(let i = 0; i < brainMethods.length; i++) {
    const brConfig = brainMethods[i].config;
    if(brConfig.cls.includes('Similarity') && brConfig.supportsPrompts) {
      validBrainRuns.push(brainMethods[i].key);
    }
   }
  return validBrainRuns;
}

function interpolationActivator() {
  const dataset = useRecoilValue(fos.dataset);
  const brainMethods = dataset.brainMethods;
  for(let i = 0; i < brainMethods.length; i++) {
    const brConfig = brainMethods[i].config;
    if(brConfig.cls.includes('Similarity') && brConfig.supportsPrompts) {
      return true;
    }
   }
  return false;
}
