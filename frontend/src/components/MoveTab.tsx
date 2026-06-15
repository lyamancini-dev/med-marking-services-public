// src/components/MoveTab.tsx
import React, { useState, useEffect } from 'react';
import {
  Box, Button, TextField, Autocomplete, IconButton, Table, TableBody,
  TableCell, TableContainer, TableHead, TableRow, Paper, Alert, Snackbar,
  CircularProgress, MenuItem, FormControl, InputLabel, Select, Card, CardContent
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import { getStores, getInventory, createMove, InventoryItem, Store } from '../api/bff';
import { playSuccessSound, playErrorSound } from '../sounds/sounds';

interface MoveRowState {
  id: string;
  service_id: number | null;
  quantity: number | string;
  rest: number;
  measure_unit_alias: string | null;
  is_allow_sale_in_parts: boolean;
}

const MoveTab: React.FC = () => {
  const [stores, setStores] = useState<Store[]>([]);
  const [storeFrom, setStoreFrom] = useState<number>(1);
  const [storeTo, setStoreTo] = useState<number | ''>('');
  const [inventory, setInventory] = useState<InventoryItem[]>([]);
  const [items, setItems] = useState<MoveRowState[]>([]);
  const [loading, setLoading] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    getStores().then(res => setStores(res.data)).catch(() => {});
  }, []);

  useEffect(() => {
    if (!storeFrom) return;
    getInventory(storeFrom).then(res => setInventory(res.data)).catch(() => {});
  }, [storeFrom]);

  const addRow = () => {
    setItems(prev => [...prev, {
      id: Date.now().toString() + Math.random(),
      service_id: null,
      quantity: '',
      rest: 0,
      measure_unit_alias: null,
      is_allow_sale_in_parts: false,
    }]);
  };

  const removeRow = (id: string) => {
    setItems(prev => prev.filter(row => row.id !== id));
  };

  const handleProductSelect = (rowId: string, product: InventoryItem | null) => {
    if (!product) {
      setItems(prev => prev.map(row => row.id === rowId ? {
        ...row, service_id: null, rest: 0, measure_unit_alias: null, is_allow_sale_in_parts: false,
      } : row));
      return;
    }
    setItems(prev => prev.map(row => row.id === rowId ? {
      ...row,
      service_id: product.id,
      rest: product.rest,
      measure_unit_alias: product.measure_unit_alias,
      is_allow_sale_in_parts: product.is_allow_sale_in_parts === 1,
    } : row));
  };

  const handleQuantityChange = (rowId: string, value: string) => {
    setItems(prev => prev.map(row => row.id === rowId ? { ...row, quantity: value } : row));
  };

  const handleSubmit = async () => {
    if (!storeFrom || storeTo === '' || items.length === 0) {
      setErrorMsg('Заполните все поля и добавьте позиции');
      return;
    }
    for (const item of items) {
      if (!item.service_id) { setErrorMsg('Выберите товар для всех позиций'); return; }
      const qty = Number(item.quantity);
      if (isNaN(qty) || qty <= 0) { setErrorMsg('Количество должно быть положительным числом'); return; }
      if (qty > item.rest) {
        const productName = inventory.find(i => i.id === item.service_id)?.name || 'Товар';
        setErrorMsg(`Недостаточно остатка для "${productName}": доступно ${item.rest}, запрошено ${qty}`);
        return;
      }
      if (!item.is_allow_sale_in_parts && !Number.isInteger(qty)) {
        const productName = inventory.find(i => i.id === item.service_id)?.name || 'Товар';
        setErrorMsg(`Товар "${productName}" нельзя делить, введите целое число`);
        return;
      }
    }

    const data = {
      store_from: storeFrom,
      store_to: Number(storeTo),
      items: items.map(i => ({ service_id: i.service_id!, quantity: Number(i.quantity) })),
    };

    setLoading(true);
    try {
      const res = await createMove(data);
      setSuccessMsg(`Черновик перемещения создан: №${res.data.doc_number} (ID ${res.data.doc_id})`);
      playSuccessSound();
      setItems([]);
      setStoreTo('');
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Ошибка создания черновика');
      playErrorSound();
    } finally {
      setLoading(false);
    }
  };

  const availableToStores = stores.filter(s => s.id !== storeFrom);

  return (
    <Box>
      <Card sx={{ mb: 3, p: 3 }}>
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          <FormControl sx={{ minWidth: 200 }}>
            <InputLabel>Склад-отправитель</InputLabel>
            <Select
              value={storeFrom}
              label="Склад-отправитель"
              onChange={(e) => setStoreFrom(Number(e.target.value))}
            >
              {stores.map(s => (
                <MenuItem key={s.id} value={s.id}>{s.name}</MenuItem>
              ))}
            </Select>
          </FormControl>

          <FormControl sx={{ minWidth: 200 }}>
            <InputLabel>Склад-получатель</InputLabel>
            <Select
              value={storeTo}
              label="Склад-получатель"
              onChange={(e) => setStoreTo(Number(e.target.value))}
            >
              {availableToStores.map(s => (
                <MenuItem key={s.id} value={s.id}>{s.name}</MenuItem>
              ))}
            </Select>
          </FormControl>
        </Box>
      </Card>

      <TableContainer component={Paper} sx={{ mb: 2 }}>
        <Table size="small">
          <TableHead>
            <TableRow sx={{ bgcolor: 'primary.main', '& th': { color: 'white', fontWeight: 600 } }}>
              <TableCell>Товар</TableCell>
              <TableCell>Остаток</TableCell>
              <TableCell>Ед. изм.</TableCell>
              <TableCell>Количество</TableCell>
              <TableCell>Действия</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {items.map(row => (
              <TableRow key={row.id} hover>
                <TableCell>
                  <Autocomplete
                    options={inventory}
                    getOptionLabel={(opt) => `${opt.name} (ID ${opt.id})`}
                    value={inventory.find(i => i.id === row.service_id) || null}
                    onChange={(_, val) => handleProductSelect(row.id, val)}
                    renderInput={(params) => <TextField {...params} size="small" />}
                    sx={{ minWidth: 200 }}
                    size="small"
                  />
                </TableCell>
                <TableCell>{row.rest}</TableCell>
                <TableCell>{row.measure_unit_alias || '-'}</TableCell>
                <TableCell>
                  <TextField
                    type="number"
                    size="small"
                    value={row.quantity}
                    onChange={(e) => handleQuantityChange(row.id, e.target.value)}
                    inputProps={{ step: row.is_allow_sale_in_parts ? '0.01' : '1', min: 0 }}
                  />
                </TableCell>
                <TableCell>
                  <IconButton onClick={() => removeRow(row.id)} color="error">
                    <DeleteIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Button variant="outlined" onClick={addRow} sx={{ mb: 2 }}>
        Добавить позицию
      </Button>
      <Box>
        <Button
          variant="contained"
          color="cta"
          onClick={handleSubmit}
          disabled={loading}
          sx={{ mr: 2 }}
        >
          {loading ? <CircularProgress size={24} /> : 'Отправить'}
        </Button>
      </Box>

      <Snackbar open={!!successMsg} autoHideDuration={6000} onClose={() => setSuccessMsg(null)}>
        <Alert severity="success">{successMsg}</Alert>
      </Snackbar>
      <Snackbar open={!!errorMsg} autoHideDuration={6000} onClose={() => setErrorMsg(null)}>
        <Alert severity="error">{errorMsg}</Alert>
      </Snackbar>
    </Box>
  );
};

export default MoveTab;