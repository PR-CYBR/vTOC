import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost/api';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const operationsAPI = {
  getAll: () => api.get('/operations/'),
  getById: (id) => api.get(`/operations/${id}`),
  create: (data) => api.post('/operations/', data),
  update: (id, data) => api.put(`/operations/${id}`, data),
  delete: (id) => api.delete(`/operations/${id}`),
};

export const missionsAPI = {
  getAll: (operationId = null) => {
    const params = operationId ? { operation_id: operationId } : {};
    return api.get('/missions/', { params });
  },
  getById: (id) => api.get(`/missions/${id}`),
  create: (data) => api.post('/missions/', data),
  update: (id, data) => api.put(`/missions/${id}`, data),
  delete: (id) => api.delete(`/missions/${id}`),
};

export const assetsAPI = {
  getAll: (assetType = null) => {
    const params = assetType ? { asset_type: assetType } : {};
    return api.get('/assets/', { params });
  },
  getById: (id) => api.get(`/assets/${id}`),
  create: (data) => api.post('/assets/', data),
  update: (id, data) => api.put(`/assets/${id}`, data),
  delete: (id) => api.delete(`/assets/${id}`),
};

export const intelAPI = {
  getAll: (missionId = null) => {
    const params = missionId ? { mission_id: missionId } : {};
    return api.get('/intel/', { params });
  },
  getById: (id) => api.get(`/intel/${id}`),
  create: (data) => api.post('/intel/', data),
  delete: (id) => api.delete(`/intel/${id}`),
};

export const agentsAPI = {
  getAll: () => api.get('/agents/'),
  getById: (id) => api.get(`/agents/${id}`),
  create: (data) => api.post('/agents/', data),
  start: (id) => api.post(`/agents/${id}/start`),
  stop: (id) => api.post(`/agents/${id}/stop`),
  delete: (id) => api.delete(`/agents/${id}`),
};

export const telemetryAPI = {
  getAssetLocations: (params = {}) => api.get('/telemetry/assets/', { params }),
  getTracks: (params = {}) => api.get('/telemetry/tracks/', { params }),
};

export default api;
