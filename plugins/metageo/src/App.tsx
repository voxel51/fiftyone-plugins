import React, { useEffect, Suspense } from "react";
import { RecoilRoot } from "recoil";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import { CssBaseline, Box, Container, CircularProgress } from "@mui/material";
import { MetageoView } from "./MetageoView";
import { usePersistence } from "./hooks/usePersistence.hook";

// Create a theme that matches FiftyOne's design
const theme = createTheme({
  palette: {
    mode: "light",
    primary: {
      main: "#1976d2",
    },
    secondary: {
      main: "#dc004e",
    },
    background: {
      default: "#fafafa",
      paper: "#ffffff",
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h6: {
      fontWeight: 600,
    },
  },
  components: {
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: "none",
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: "none",
          borderRadius: 8,
        },
      },
    },
  },
});

// Inner component that uses the persistence hook
function AppContent() {
  // Enable automatic state persistence
  usePersistence();
  
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ minHeight: "100vh", bgcolor: "background.default" }}>
        <Container maxWidth="xl" sx={{ py: 3 }}>
          <Suspense fallback={
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '200px' }}>
              <CircularProgress />
            </Box>
          }>
            <MetageoView />
          </Suspense>
        </Container>
      </Box>
    </ThemeProvider>
  );
}

export default function App() {
  return (
    <RecoilRoot>
      <AppContent />
    </RecoilRoot>
  );
}
