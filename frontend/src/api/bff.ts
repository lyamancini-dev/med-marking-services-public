import axios from 'axios';

const apiClient = axios.create({
  baseURL: process.env.REACT_APP_BFF_URL || 'http://localhost:8002/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Типы ответов
export interface Store {
  id: number;
  name: string;
}

export interface InventoryItem {
  id: number;
  name: string;
  gtin: string | null;
  is_marked: number;
  rest: number;
  store_id: number;
  sgtins: string[];
  measure_unit_code: string | null;
  measure_unit_alias: string | null;
  is_allow_sale_in_parts: number | null;
}

export interface DropoutReason {
  code: string;
  name: string;
}

export interface WriteOffRow {
  service_id: number;
  quantity: number;
  sgtins: string[];
}

export interface WriteOffRequest {
  store_from: number;
  store_to: number;
  items: WriteOffRow[];
  source_doc_date: string; // yyyy-mm-dd
  dropout_reason: string;
  source_doc_type: string;
  source_doc_num: string;
  source_doc_name: string;
  doctype_id: number;
}

export interface MoveRequest {
  store_from: number;
  store_to: number;
  items: { service_id: number; quantity: number }[];
}

export interface OperationResponse {
  doc_id: number;
  doc_number: string;
  saga_id: string | null;
  saga_status: string | null;
  saga_errors: string[] | null;
}

export interface DocumentListItem {
  id: number;
  doctype_id: number;
  number: string;
  date_fact: number;
  is_close: number;
  store_from: number;
  store_to: number;
  saga_id: string | null;
  gis_mt_status: string | null;
  gis_mt_errors: string | null;
}

export interface SagaStatus {
  saga_id: string;
  status: string;
  doc_id: string;
  errors: string[] | null;
}

// API-функции
export const getStores = () => apiClient.get<Store[]>('/stores');

export const getInventory = (store_id?: number, search?: string) =>
  apiClient.get<InventoryItem[]>('/inventory', { params: { store_id, search } });

export const getDropoutReasons = () =>
  apiClient.get<DropoutReason[]>('/dictionaries/dropout-reasons');

export const createMove = (data: MoveRequest) =>
  apiClient.post<OperationResponse>('/operations/move', data);

export const createWriteOff = (data: WriteOffRequest) =>
  apiClient.post<OperationResponse>('/operations/write-off', data);

export const approveDocument = (doc_id: number) =>
  apiClient.post(`/documents/${doc_id}/approve`);

export const getDocuments = (store_id?: number, limit?: number) =>
  apiClient.get<DocumentListItem[]>('/documents', { params: { store_id, limit } });

export const getSagaStatus = (saga_id: string) =>
  apiClient.get<SagaStatus>(`/operations/${saga_id}/status`);