import { createTheme } from '@mui/material/styles';

const theme = createTheme({
  palette: {
    primary: {
      main: '#5C6BC0',
      contrastText: '#ffffff',
    },
    secondary: {
      main: '#26C6DA',
      contrastText: '#ffffff',
    },
    error: {
      main: '#EF5350',
    },
    background: {
      default: '#F5F5F5',
      paper: '#ffffff',
    },
    text: {
      primary: '#263238',
      secondary: '#546E7A',
    },
    cta: {
      main: '#FF7043',
      contrastText: '#ffffff',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h1: { fontWeight: 600 },
    h2: { fontWeight: 600 },
    h3: { fontWeight: 600 },
    h4: { fontWeight: 600 },
    h5: { fontWeight: 600 },
    h6: { fontWeight: 600 },
    body1: { fontWeight: 400, lineHeight: 1.6 },
    button: { fontWeight: 500, letterSpacing: '0.3px' },
  },
  shape: {
    borderRadius: 12,
  },
  spacing: 8,
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          textTransform: 'none',
          boxShadow: '0px 4px 8px rgba(0,0,0,0.1)',
          transition: 'all 0.2s ease-in-out',
          '&:hover': {
            transform: 'translateY(-1px)',
            boxShadow: '0px 6px 12px rgba(0,0,0,0.15)',
          },
        },
        containedPrimary: {
          background: 'linear-gradient(135deg, #5C6BC0 0%, #3F51B5 100%)',
          color: '#ffffff',
          '&:hover': {
            background: 'linear-gradient(135deg, #3F51B5 0%, #303F9F 100%)',
          },
        },
        containedSecondary: {
          background: 'linear-gradient(135deg, #26C6DA 0%, #00ACC1 100%)',
          color: '#ffffff',
          '&:hover': {
            background: 'linear-gradient(135deg, #00ACC1 0%, #0097A7 100%)',
          },
        },
        outlined: {
          border: '1px solid #B0BEC5',
          color: '#37474F',
          '&:hover': {
            borderColor: '#5C6BC0',
            backgroundColor: 'rgba(92,107,192,0.04)',
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 16,
          boxShadow: '0px 4px 12px rgba(0,0,0,0.06)',
          border: '1px solid rgba(0,0,0,0.04)',
          transition: 'all 0.2s ease',
          '&:hover': {
            boxShadow: '0px 8px 24px rgba(0,0,0,0.1)',
          },
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: 12,
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 8,
          },
        },
      },
    },
    MuiTableContainer: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          boxShadow: '0px 2px 8px rgba(0,0,0,0.06)',
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: {
          borderBottom: '1px solid #ECEFF1',
        },
      },
    },
  },
});

export default theme;