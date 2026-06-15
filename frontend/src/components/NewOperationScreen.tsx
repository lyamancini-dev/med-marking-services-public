// src/components/NewOperationScreen.tsx
import React, { useState } from 'react';
import { Box, Tabs, Tab } from '@mui/material';
import MoveTab from './MoveTab';
import WriteOffTab from './WriteOffTab';

const NewOperationScreen: React.FC = () => {
  const [tab, setTab] = useState(0);

  return (
    <Box>
      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 2 }}>
        <Tab label="Перемещение" />
        <Tab label="Списание" />
      </Tabs>
      {tab === 0 && <MoveTab />}
      {tab === 1 && <WriteOffTab />}
    </Box>
  );
};

export default NewOperationScreen;