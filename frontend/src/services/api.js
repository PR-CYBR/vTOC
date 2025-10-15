import axios from 'axios';
import { createMockProvider } from './mocks';

const USE_MOCKS = String(process.env.REACT_APP_USE_MOCKS || '').toLowerCase() === 'true';

const createAxiosProvider = () => {
  const API_URL = process.env.REACT_APP_API_URL || 'http://localhost/api';

  const client = axios.create({
    baseURL: API_URL,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  return {
    mode: 'http',
    client,
    operations: {
      getAll: () => client.get('/operations/'),
      getById: (id) => client.get(`/operations/${id}`),
      create: (data) => client.post('/operations/', data),
      update: (id, data) => client.put(`/operations/${id}`, data),
      delete: (id) => client.delete(`/operations/${id}`),
    },
    missions: {
      getAll: (operationId = null) => {
        const params = operationId ? { operation_id: operationId } : {};
        return client.get('/missions/', { params });
      },
      getById: (id) => client.get(`/missions/${id}`),
      create: (data) => client.post('/missions/', data),
      update: (id, data) => client.put(`/missions/${id}`, data),
      delete: (id) => client.delete(`/missions/${id}`),
    },
    assets: {
      getAll: (assetType = null) => {
        const params = assetType ? { asset_type: assetType } : {};
        return client.get('/assets/', { params });
      },
      getById: (id) => client.get(`/assets/${id}`),
      create: (data) => client.post('/assets/', data),
      update: (id, data) => client.put(`/assets/${id}`, data),
      delete: (id) => client.delete(`/assets/${id}`),
    },
    intel: {
      getAll: (missionId = null) => {
        const params = missionId ? { mission_id: missionId } : {};
        return client.get('/intel/', { params });
      },
      getById: (id) => client.get(`/intel/${id}`),
      create: (data) => client.post('/intel/', data),
      delete: (id) => client.delete(`/intel/${id}`),
    },
    agents: {
      getAll: () => client.get('/agents/'),
      getById: (id) => client.get(`/agents/${id}`),
      create: (data) => client.post('/agents/', data),
      start: (id) => client.post(`/agents/${id}/start`),
      stop: (id) => client.post(`/agents/${id}/stop`),
      delete: (id) => client.delete(`/agents/${id}`),
    },
    telemetry: {
      getAll: (filters = {}) => client.get('/telemetry/', { params: filters }),
    },
  };
};

const provider = USE_MOCKS ? createMockProvider() : createAxiosProvider();

export const apiProvider = provider;
export const useApi = () => provider;

export const operationsAPI = provider.operations;
export const missionsAPI = provider.missions;
export const assetsAPI = provider.assets;
export const intelAPI = provider.intel;
export const agentsAPI = provider.agents;
export const telemetryAPI = provider.telemetry;

export default provider.client;
