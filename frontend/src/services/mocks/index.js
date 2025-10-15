import { defaultMockData } from './datasets';

const STORAGE_KEY = 'vtoc-mock-data';
const RESPONSE_DELAY = 200;

const deepClone = (value) => JSON.parse(JSON.stringify(value));

const getStorage = () => {
  if (typeof window !== 'undefined' && window.localStorage) {
    return window.localStorage;
  }
  return null;
};

let memoryStore = null;

const loadFromStorage = () => {
  const storage = getStorage();

  if (storage) {
    const serialized = storage.getItem(STORAGE_KEY);
    if (serialized) {
      try {
        return JSON.parse(serialized);
      } catch (error) {
        console.warn('[MockAPI] Failed to parse stored data, resetting to defaults.', error);
        storage.removeItem(STORAGE_KEY);
      }
    }
  } else if (memoryStore) {
    return deepClone(memoryStore);
  }

  return deepClone(defaultMockData);
};

const saveToStorage = (data) => {
  const storage = getStorage();
  const snapshot = deepClone(data);

  if (storage) {
    storage.setItem(STORAGE_KEY, JSON.stringify(snapshot));
  } else {
    memoryStore = snapshot;
  }
};

const respond = (payload) =>
  new Promise((resolve) => {
    setTimeout(() => {
      resolve({ data: deepClone(payload) });
    }, RESPONSE_DELAY);
  });

const rejectWithMessage = (message) =>
  Promise.reject(new Error(`[MockAPI] ${message}`));

export const createMockProvider = () => {
  const database = loadFromStorage();
  const idCounters = {};

  const ensureCounter = (collection) => {
    if (!idCounters[collection]) {
      const nextId = database[collection].reduce((max, item) => {
        const numericId = Number(item.id);
        return Number.isNaN(numericId) ? max : Math.max(max, numericId);
      }, 0);
      idCounters[collection] = nextId + 1;
    }
  };

  const nextId = (collection) => {
    ensureCounter(collection);
    const current = idCounters[collection];
    idCounters[collection] += 1;
    return current;
  };

  const persist = () => {
    saveToStorage(database);
  };

  const findById = (collection, id) =>
    database[collection].find((item) => String(item.id) === String(id));

  const upsertEntity = (collection, entity) => {
    const existingIndex = database[collection].findIndex(
      (item) => String(item.id) === String(entity.id),
    );

    if (existingIndex >= 0) {
      database[collection][existingIndex] = entity;
    } else {
      database[collection].push(entity);
    }

    persist();
    return respond(entity);
  };

  const removeEntity = (collection, id) => {
    const index = database[collection].findIndex((item) => String(item.id) === String(id));
    if (index === -1) {
      return rejectWithMessage(`${collection} entity ${id} not found`);
    }

    const [removed] = database[collection].splice(index, 1);
    persist();
    return respond(removed);
  };

  const operations = {
    getAll: () => respond(database.operations),
    getById: (id) => {
      const operation = findById('operations', id);
      if (!operation) {
        return rejectWithMessage(`Operation ${id} not found`);
      }
      return respond(operation);
    },
    create: (data) => {
      const now = new Date().toISOString();
      const operation = {
        id: nextId('operations'),
        code_name: data.code_name || `OP-${Math.random().toString(36).slice(2, 6).toUpperCase()}`,
        name: data.name || 'Untitled Operation',
        status: data.status || 'planning',
        priority: data.priority || 'medium',
        created_at: data.created_at || now,
        updated_at: now,
        ...data,
      };
      return upsertEntity('operations', operation);
    },
    update: (id, data) => {
      const existing = findById('operations', id);
      if (!existing) {
        return rejectWithMessage(`Operation ${id} not found`);
      }
      const updated = {
        ...existing,
        ...data,
        updated_at: new Date().toISOString(),
      };
      return upsertEntity('operations', updated);
    },
    delete: (id) => removeEntity('operations', id),
  };

  const missions = {
    getAll: (operationId = null) => {
      const results = operationId
        ? database.missions.filter((mission) => String(mission.operation_id) === String(operationId))
        : database.missions;
      return respond(results);
    },
    getById: (id) => {
      const mission = findById('missions', id);
      if (!mission) {
        return rejectWithMessage(`Mission ${id} not found`);
      }
      return respond(mission);
    },
    create: (data) => {
      const now = new Date().toISOString();
      const mission = {
        id: nextId('missions'),
        status: data.status || 'pending',
        priority: data.priority || 'medium',
        created_at: data.created_at || now,
        updated_at: now,
        ...data,
      };
      return upsertEntity('missions', mission);
    },
    update: (id, data) => {
      const existing = findById('missions', id);
      if (!existing) {
        return rejectWithMessage(`Mission ${id} not found`);
      }
      const updated = {
        ...existing,
        ...data,
        updated_at: new Date().toISOString(),
      };
      return upsertEntity('missions', updated);
    },
    delete: (id) => removeEntity('missions', id),
  };

  const assets = {
    getAll: (assetType = null) => {
      const results = assetType
        ? database.assets.filter((asset) => asset.asset_type === assetType)
        : database.assets;
      return respond(results);
    },
    getById: (id) => {
      const asset = findById('assets', id);
      if (!asset) {
        return rejectWithMessage(`Asset ${id} not found`);
      }
      return respond(asset);
    },
    create: (data) => {
      const asset = {
        id: nextId('assets'),
        status: data.status || 'active',
        ...data,
      };
      return upsertEntity('assets', asset);
    },
    update: (id, data) => {
      const existing = findById('assets', id);
      if (!existing) {
        return rejectWithMessage(`Asset ${id} not found`);
      }
      const updated = {
        ...existing,
        ...data,
      };
      return upsertEntity('assets', updated);
    },
    delete: (id) => removeEntity('assets', id),
  };

  const agents = {
    getAll: () => respond(database.agents),
    getById: (id) => {
      const agent = findById('agents', id);
      if (!agent) {
        return rejectWithMessage(`Agent ${id} not found`);
      }
      return respond(agent);
    },
    create: (data) => {
      const now = new Date().toISOString();
      const agent = {
        id: nextId('agents'),
        status: data.status || 'idle',
        last_run: data.last_run || null,
        created_at: now,
        updated_at: now,
        ...data,
      };
      return upsertEntity('agents', agent);
    },
    start: (id) => {
      const agent = findById('agents', id);
      if (!agent) {
        return rejectWithMessage(`Agent ${id} not found`);
      }
      const now = new Date().toISOString();
      const updated = {
        ...agent,
        status: 'running',
        last_run: now,
        updated_at: now,
      };
      return upsertEntity('agents', updated);
    },
    stop: (id) => {
      const agent = findById('agents', id);
      if (!agent) {
        return rejectWithMessage(`Agent ${id} not found`);
      }
      const updated = {
        ...agent,
        status: 'idle',
        updated_at: new Date().toISOString(),
      };
      return upsertEntity('agents', updated);
    },
    update: (id, data) => {
      const existing = findById('agents', id);
      if (!existing) {
        return rejectWithMessage(`Agent ${id} not found`);
      }
      const updated = {
        ...existing,
        ...data,
        updated_at: new Date().toISOString(),
      };
      return upsertEntity('agents', updated);
    },
    delete: (id) => removeEntity('agents', id),
  };

  const intel = {
    getAll: (missionId = null) => {
      const results = missionId
        ? database.intel.filter((record) => String(record.mission_id) === String(missionId))
        : database.intel;
      return respond(results);
    },
    getById: (id) => {
      const record = findById('intel', id);
      if (!record) {
        return rejectWithMessage(`Intel record ${id} not found`);
      }
      return respond(record);
    },
    create: (data) => {
      const now = new Date().toISOString();
      const record = {
        id: nextId('intel'),
        report_date: data.report_date || now,
        ...data,
      };
      return upsertEntity('intel', record);
    },
    delete: (id) => removeEntity('intel', id),
  };

  const telemetry = {
    getAll: (filters = {}) => {
      const { asset_id: assetId, metric } = filters;
      let results = database.telemetry;

      if (assetId) {
        results = results.filter((entry) => String(entry.asset_id) === String(assetId));
      }
      if (metric) {
        results = results.filter((entry) => entry.metric === metric);
      }

      return respond(results);
    },
    append: (data) => {
      const entry = {
        id: nextId('telemetry'),
        recorded_at: data.recorded_at || new Date().toISOString(),
        ...data,
      };
      return upsertEntity('telemetry', entry);
    },
  };

  return {
    mode: 'mock',
    client: { baseURL: 'mock://local' },
    operations,
    missions,
    assets,
    agents,
    intel,
    telemetry,
  };
};
