import { Box, Typography, TextField } from "@mui/material";

export default function ExampleCustomView(props) {
  const { path, validationErrors, onChange, data, schema } = props;
  const { view = {}, default: defaultValue } = schema;
  const { label, description, caption } = view;
  console.log(validationErrors);
  return (
    <Box>
      <Typography>{label}</Typography>
      {description && <Typography>{description}</Typography>}
      <TextField
        defaultValue={data ?? defaultValue}
        onChange={(e) => onChange(path, e.target.value)}
        size="small"
        multiline
        rows={3}
        fullWidth
      />
      {caption && <Typography>{caption}</Typography>}
      {Array.isArray(validationErrors) && validationErrors.length > 0 && (
        <Typography variant="body2" color="error.main">
          {validationErrors.map(({ reason }) => reason).join(", ")}
        </Typography>
      )}
    </Box>
  );
}
