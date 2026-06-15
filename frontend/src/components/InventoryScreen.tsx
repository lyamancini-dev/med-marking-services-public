import React, { useEffect, useState } from 'react';
import {
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Paper, Typography, FormControl, InputLabel, Select, MenuItem, Box, Card, CardContent
} from '@mui/material';
import { getStores, getInventory, Store, InventoryItem } from '../api/bff';

const InventoryScreen: React.FC = () => {
  const [stores, setStores] = useState<Store[]>([]);
  const [selectedStore, setSelectedStore] = useState<number | ''>('');
  const [items, setItems] = useState<InventoryItem[]>([]);

  useEffect(() => {
    getStores().then(res => setStores(res.data));
  }, []);

  useEffect(() => {
    if (selectedStore === '') return;
    getInventory(selectedStore).then(res => setItems(res.data));
  }, [selectedStore]);

  return (
    <Box>
      <Card sx={{ mb: 3, p: 2 }}>
        <FormControl fullWidth>
          <InputLabel>Склад</InputLabel>
          <Select
            value={selectedStore}
            label="Склад"
            onChange={(e) => setSelectedStore(Number(e.target.value))}
          >
            {stores.map(s => (
              <MenuItem key={s.id} value={s.id}>{s.name}</MenuItem>
            ))}
          </Select>
        </FormControl>
      </Card>

      {selectedStore === '' ? (
        <Card>
          <CardContent>
            <Typography variant="h6" color="textSecondary">Выберите склад для просмотра ТМЦ</Typography>
          </CardContent>
        </Card>
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow sx={{ bgcolor: 'primary.main', '& th': { color: 'white' } }}>
                <TableCell>ID</TableCell>
                <TableCell>Наименование</TableCell>
                <TableCell>GTIN</TableCell>
                <TableCell>Марк.</TableCell>
                <TableCell>Остаток</TableCell>
                <TableCell>Ед. изм.</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {items.map(item => (
                <TableRow key={item.id} hover>
                  <TableCell>{item.id}</TableCell>
                  <TableCell>{item.name}</TableCell>
                  <TableCell>{item.gtin || '-'}</TableCell>
                  <TableCell>{item.is_marked ? 'Да' : 'Нет'}</TableCell>
                  <TableCell>{item.rest}</TableCell>
                  <TableCell>{item.measure_unit_alias || '-'}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Box>
  );
};

export default InventoryScreen;