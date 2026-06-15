// src/components/JournalScreen.tsx
import React, { useEffect, useState } from 'react';
import {
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Paper, Button, Typography, Box, Chip, Card, CardContent
} from '@mui/material';
import { getDocuments, approveDocument, DocumentListItem } from '../api/bff';
import { playSuccessSound, playErrorSound } from '../sounds/sounds';

const statusColors: { [key: string]: string } = {
  PENDING: '#FFA726',
  SENT: '#FFA726',
  CHECKED_OK: '#66BB6A',
  ERROR: '#EF5350',
  CHECKED_NOT_OK: '#EF5350',
  TIMEOUT: '#EF5350',
};

interface Props {
  role: 'nurse' | 'senior';
}

const JournalScreen: React.FC<Props> = ({ role }) => {
  const [docs, setDocs] = useState<DocumentListItem[]>([]);

  const loadDocs = () => {
    getDocuments(undefined, 50)
      .then(res => setDocs(res.data))
      .catch(() => {});
  };

  useEffect(() => {
    loadDocs();
  }, []);

  const handleApprove = async (docId: number) => {
    try {
      await approveDocument(docId);
      playSuccessSound();
      loadDocs();
    } catch (e) {
      playErrorSound();
    }
  };

  return (
    <Box>
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h5" fontWeight={600}>
            Журнал документов
          </Typography>
        </CardContent>
      </Card>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow sx={{ bgcolor: 'primary.main', '& th': { color: 'white', fontWeight: 600 } }}>
              <TableCell>ID</TableCell>
              <TableCell>Номер</TableCell>
              <TableCell>Тип</TableCell>
              <TableCell>Дата факт</TableCell>
              <TableCell>Закрыт</TableCell>
              <TableCell>Статус ГИС МТ</TableCell>
              <TableCell>Ошибки</TableCell>
              {role === 'senior' && <TableCell>Действия</TableCell>}
            </TableRow>
          </TableHead>
          <TableBody>
            {docs.map(doc => (
              <TableRow key={doc.id} hover>
                <TableCell>{doc.id}</TableCell>
                <TableCell>{doc.number}</TableCell>
                <TableCell>{doc.doctype_id === 2 ? 'Списание' : 'Перемещение'}</TableCell>
                <TableCell>{doc.date_fact}</TableCell>
                <TableCell>{doc.is_close ? 'Да' : 'Нет'}</TableCell>
                <TableCell>
                  {doc.gis_mt_status ? (
                    <Chip
                      label={doc.gis_mt_status}
                      size="small"
                      sx={{
                        bgcolor: statusColors[doc.gis_mt_status] || 'grey',
                        color: 'white',
                      }}
                    />
                  ) : '-'}
                </TableCell>
                <TableCell>{doc.gis_mt_errors || '-'}</TableCell>
                {role === 'senior' && (
                  <TableCell>
                    {doc.is_close === 0 && (
                      <Button
                        size="small"
                        variant="contained"
                        color="cta"
                        onClick={() => handleApprove(doc.id)}
                      >
                        Утвердить
                      </Button>
                    )}
                  </TableCell>
                )}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

export default JournalScreen;