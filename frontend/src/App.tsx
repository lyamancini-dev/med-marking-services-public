// src/App.tsx
import React, { useState } from 'react';
import { ThemeProvider, CssBaseline } from '@mui/material';
import theme from './theme';
import Layout from './components/Layout';
import InventoryScreen from './components/InventoryScreen';
import NewOperationScreen from './components/NewOperationScreen';
import JournalScreen from './components/JournalScreen';

const App: React.FC = () => {
  const [tab, setTab] = useState(0);
  const [role, setRole] = useState<'nurse' | 'senior'>('nurse');

  const renderScreen = () => {
    switch (tab) {
      case 0:
        return <InventoryScreen />;
      case 1:
        return <NewOperationScreen />;
      case 2:
        return role === 'senior' ? <JournalScreen role={role} /> : null;
      default:
        return null;
    }
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Layout
        currentTab={tab}
        onTabChange={setTab}
        role={role}
        onRoleChange={setRole}
      >
        {renderScreen()}
      </Layout>
    </ThemeProvider>
  );
};

export default App;