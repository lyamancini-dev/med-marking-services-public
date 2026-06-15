// src/components/WriteOffTab.tsx
import React, { useState, useEffect } from 'react';
import {
  Box, Button, TextField, MenuItem, Typography, IconButton,
  Autocomplete, CircularProgress, Alert, Paper, Table, TableBody,
  TableCell, TableContainer, TableHead, TableRow, Snackbar,
  FormControl, InputLabel, Select, Card
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import {
  getStores, getInventory, getDropoutReasons, createWriteOff,
  InventoryItem, DropoutReason, WriteOffRequest, Store
} from '../api/bff';
import { playSuccessSound, playErrorSound } from '../sounds/sounds';

interface WriteOffRowState {
  id: string;
  service_id: number | null;
  quantity: number | string;
  sgtins: string[];
  is_marked: boolean;
  rest: number;
  measure_unit_alias: string | null;
  is_allow_sale_in_parts: boolean;
}

const WriteOffTab: React.FC = () => {
  const [stores, setStores] = useState<Store[]>([]);
  const [storeFrom, setStoreFrom] = useState<number>(1);
  const [inventory, setInventory] = useState<InventoryItem[]>([]);
  const [reasons, setReasons] = useState<DropoutReason[]>([]);
  const [dropoutReason, setDropoutReason] = useState<string>('MEDICAL_USE');
  const [sourceDocDate, setSourceDocDate] = useState<string>('');
  const [items, setItems] = useState<WriteOffRowState[]>([]);
  const [loading, setLoading] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    getStores().then(res => setStores(res.data)).catch(() => {});
    getDropoutReasons().then(res => setReasons(res.data)).catch(() => {});
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
      sgtins: [],
      is_marked: false,
      rest: 0,
      measure_unit_alias: null,
      is_allow_sale_in_parts: false,
    }]);
  };

  const removeRow = (id: string) => {
    setItems(prev => prev.filter(r => r.id !== id));
  };

  const handleProductSelect = (rowId: string, product: InventoryItem | null) => {
    if (!product) {
      setItems(prev => prev.map(r => r.id === rowId ? {
        ...r, service_id: null, is_marked: false, rest: 0, measure_unit_alias: null, is_allow_sale_in_parts: false
      } : r));
      return;
    }
    setItems(prev => prev.map(r => r.id === rowId ? {
      ...r,
      service_id: product.id,
      is_marked: product.is_marked === 1,
      rest: product.rest,
      measure_unit_alias: product.measure_unit_alias,
      is_allow_sale_in_parts: product.is_allow_sale_in_parts === 1,
    } : r));
  };

  const handleQuantityChange = (rowId: string, value: string) => {
    setItems(prev => prev.map(r => r.id === rowId ? { ...r, quantity: value } : r));
  };

  const addSgtin = (rowId: string, sgtin: string) => {
    const clean = sgtin.trim();
    if (!clean) return;
    setItems(prev => prev.map(r => {
      if (r.id !== rowId) return r;
      if (r.sgtins.includes(clean)) {
        playErrorSound();
        setErrorMsg('Такой SGTIN уже добавлен');
        return r;
      }
      if (r.quantity && r.sgtins.length >= Number(r.quantity)) {
        playErrorSound();
        setErrorMsg('Количество SGTIN не может превышать количество товара');
        return r;
      }
      playSuccessSound();
      const updated = { ...r, sgtins: [...r.sgtins, clean] };
      setTimeout(() => {
        const nextInput = document.getElementById(`sgtin-input-${rowId}`);
        if (nextInput) nextInput.focus();
      }, 0);
      return updated;
    }));
  };

  const handleSgtinKeyDown = (e: React.KeyboardEvent<HTMLInputElement>, rowId: string) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      const input = e.target as HTMLInputElement;
      addSgtin(rowId, input.value);
      input.value = '';
    }
  };

  const generateActNumber = (): string => {
    const now = new Date();
    const yyyy = now.getFullYear();
    const mm = String(now.getMonth() + 1).padStart(2, '0');
    const dd = String(now.getDate()).padStart(2, '0');
    const random = Math.floor(Math.random() * 900) + 100;
    return `АКТ-${yyyy}${mm}${dd}-${random}`;
  };

  const handleSubmit = async () => {
    if (!storeFrom || !sourceDocDate || items.length === 0) {
      setErrorMsg('Заполните все обязательные поля и добавьте позиции');
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
      if (item.is_marked && item.sgtins.length !== qty) {
        const productName = inventory.find(i => i.id === item.service_id)?.name || 'Товар';
        setErrorMsg(`Для товара "${productName}" необходимо ввести ровно ${qty} SGTIN`);
        return;
      }
      if (!item.is_allow_sale_in_parts && !Number.isInteger(qty)) {
        const productName = inventory.find(i => i.id === item.service_id)?.name || 'Товар';
        setErrorMsg(`Товар "${productName}" нельзя делить, введите целое число`);
        return;
      }
    }

    const requestData: WriteOffRequest = {
      store_from: storeFrom,
      store_to: 0,
      items: items.map(item => ({
        service_id: item.service_id!,
        quantity: Number(item.quantity),
        sgtins: item.sgtins, // <-- ИСПРАВЛЕНИЕ: убрана замена \x1d на \\u001d
      })),
      source_doc_date: sourceDocDate,
      dropout_reason: dropoutReason,
      source_doc_type: 'OTHER',
      source_doc_num: generateActNumber(),
      source_doc_name: 'Акт списания',
      doctype_id: 2,
    };

    setLoading(true);
    try {
      const res = await createWriteOff(requestData);
      setSuccessMsg(`Черновик списания создан: №${res.data.doc_number} (ID ${res.data.doc_id})`);
      playSuccessSound();
      setItems([]);
      setSourceDocDate('');
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Ошибка создания черновика');
      playErrorSound();
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Card sx={{ mb: 3, p: 3 }}>
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          <FormControl sx={{ minWidth: 200 }}>
            <InputLabel>Склад списания</InputLabel>
            <Select
              value={storeFrom}
              label="Склад списания"
              onChange={(e) => setStoreFrom(Number(e.target.value))}
            >
              {stores.map(s => (
                <MenuItem key={s.id} value={s.id}>{s.name}</MenuItem>
              ))}
            </Select>
          </FormControl>

          <FormControl sx={{ minWidth: 200 }}>
            <InputLabel>Причина выбытия</InputLabel>
            <Select
              value={dropoutReason}
              label="Причина выбытия"
              onChange={(e) => setDropoutReason(e.target.value)}
            >
              {reasons.map(r => (
                <MenuItem key={r.code} value={r.code}>{r.name}</MenuItem>
              ))}
            </Select>
          </FormControl>

          <TextField
            label="Дата акта"
            type="date"
            value={sourceDocDate}
            onChange={(e) => setSourceDocDate(e.target.value)}
            InputLabelProps={{ shrink: true }}
          />
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
              <TableCell>SGTIN (для маркированных)</TableCell>
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
                  {row.is_marked && (
                    <Box>
                      {row.sgtins.map((s, idx) => (
                        <Typography key={idx} variant="body2">{s}</Typography>
                      ))}
                      <TextField
                        id={`sgtin-input-${row.id}`}
                        placeholder="Отсканируйте SGTIN"
                        size="small"
                        onKeyDown={(e: any) => handleSgtinKeyDown(e, row.id)}
                        sx={{ mt: 1 }}
                      />
                    </Box>
                  )}
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
          {loading ? <CircularProgress size={24} /> : 'Отправить черновик'}
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

export default WriteOffTab;