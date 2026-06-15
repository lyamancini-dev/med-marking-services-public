import { useState, useEffect } from 'react';
import { getStores, getDropoutReasons, Store, DropoutReason } from '../api/bff';

export function useStores() {
  const [stores, setStores] = useState<Store[]>([]);
  useEffect(() => {
    getStores().then(res => setStores(res.data)).catch(console.error);
  }, []);
  return { stores };
}

export function useDropoutReasons() {
  const [reasons, setReasons] = useState<DropoutReason[]>([]);
  useEffect(() => {
    getDropoutReasons().then(res => setReasons(res.data)).catch(console.error);
  }, []);
  return reasons;
}