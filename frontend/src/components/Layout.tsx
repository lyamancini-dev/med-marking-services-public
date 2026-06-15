import React from 'react';
import {
  AppBar, Toolbar, Typography, Container, Box,
  Tabs, Tab, Select, MenuItem, FormControl, InputLabel
} from '@mui/material';

interface LayoutProps {
  currentTab: number;
  onTabChange: (newTab: number) => void;
  role: 'nurse' | 'senior';
  onRoleChange: (role: 'nurse' | 'senior') => void;
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({
  currentTab, onTabChange, role, onRoleChange, children
}) => {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <AppBar
        position="static"
        sx={{
          background: 'linear-gradient(135deg, #5C6BC0 0%, #3F51B5 100%)',
          boxShadow: '0px 4px 12px rgba(0,0,0,0.15)',
        }}
      >
        <Toolbar sx={{ gap: 2 }}>
          <Typography
            variant="h5"
            fontWeight={600}
            letterSpacing="-0.5px"
            sx={{ flexGrow: 1 }}
          >
            Управление ТМЦ - ГИС МТ
          </Typography>

          <FormControl sx={{ minWidth: 150 }} size="small">
            <InputLabel id="role-label" sx={{ color: 'white' }}>Роль</InputLabel>
            <Select
              labelId="role-label"
              value={role}
              onChange={(e) => onRoleChange(e.target.value as any)}
              label="Роль"
              sx={{ color: 'white', '.MuiOutlinedInput-notchedOutline': { borderColor: 'rgba(255,255,255,0.5)' } }}
            >
              <MenuItem value="nurse">Медсестра</MenuItem>
              <MenuItem value="senior">Старшая м/с</MenuItem>
            </Select>
          </FormControl>
        </Toolbar>
        <Tabs
          value={currentTab}
          onChange={(_, v) => onTabChange(v)}
          textColor="inherit"
          indicatorColor="secondary"
          sx={{
            '& .MuiTab-root': { color: 'rgba(255,255,255,0.8)' },
            '& .Mui-selected': { color: 'white' },
          }}
        >
          <Tab label="ТМЦ" />
          <Tab label="Новая операция" />
          {role === 'senior' && <Tab label="Журнал" />}
        </Tabs>
      </AppBar>
      <Container maxWidth="xl" sx={{ flexGrow: 1, py: 4 }}>
        {children}
      </Container>
    </Box>
  );
};

export default Layout;