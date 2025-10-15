import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import api from './api';

export interface AgentTool {
  name: string;
  description: string;
  signature: Record<string, unknown>;
  category?: string;
}

export interface AgentActionRequest {
  tool_name: string;
  action_input: Record<string, unknown>;
  metadata?: Record<string, unknown>;
}

export interface AgentActionResponse {
  action_id: string;
  status: 'queued' | 'running' | 'succeeded' | 'failed';
  result?: Record<string, unknown>;
  message?: string;
}

export interface AgentActionAudit {
  id: number | string;
  action_id: string;
  tool_name: string;
  status: 'queued' | 'running' | 'succeeded' | 'failed';
  request_payload?: Record<string, unknown> | null;
  response_payload?: Record<string, unknown> | null;
  error_message?: string | null;
  created_at: string;
  updated_at: string;
  completed_at?: string | null;
}

const TOOL_QUERY_KEY = ['agent-actions', 'tools'];
const AUDIT_QUERY_KEY = ['agent-actions', 'audits'];

export const useAgentTools = () =>
  useQuery<AgentTool[]>({
    queryKey: TOOL_QUERY_KEY,
    queryFn: async () => {
      const response = await api.get('/api/v1/agent-actions/tools');
      return response.data;
    },
    staleTime: 5 * 60 * 1000,
  });

export const useAgentActionAudits = () =>
  useQuery<AgentActionAudit[]>({
    queryKey: AUDIT_QUERY_KEY,
    queryFn: async () => {
      const response = await api.get('/api/v1/agent-actions/audits');
      return response.data;
    },
    refetchInterval: 15_000,
  });

interface MutationContext {
  previous?: AgentActionAudit[];
  optimisticId: string;
}

export const useExecuteAgentAction = () => {
  const queryClient = useQueryClient();

  return useMutation<AgentActionResponse, unknown, AgentActionRequest, MutationContext>({
    mutationFn: async (payload) => {
      const response = await api.post('/api/v1/agent-actions/execute', payload);
      return response.data;
    },
    onMutate: async (payload) => {
      const optimisticId = `optimistic-${Date.now()}`;
      await queryClient.cancelQueries({ queryKey: AUDIT_QUERY_KEY });
      const previous = queryClient.getQueryData<AgentActionAudit[]>(AUDIT_QUERY_KEY) ?? [];
      const optimistic: AgentActionAudit = {
        id: optimisticId,
        action_id: optimisticId,
        tool_name: payload.tool_name,
        status: 'queued',
        request_payload: payload.action_input,
        response_payload: null,
        error_message: null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        completed_at: null,
      };
      queryClient.setQueryData(AUDIT_QUERY_KEY, [optimistic, ...previous]);
      return { previous, optimisticId };
    },
    onError: (_error, _payload, context) => {
      if (context?.previous) {
        queryClient.setQueryData(AUDIT_QUERY_KEY, context.previous);
      }
    },
    onSuccess: (data, _payload, context) => {
      queryClient.setQueryData<AgentActionAudit[]>(AUDIT_QUERY_KEY, (current = []) => {
        return current.map((audit) =>
          audit.id === context?.optimisticId
            ? {
                ...audit,
                action_id: data.action_id,
                status: data.status,
                response_payload: data.result ?? audit.response_payload,
                updated_at: new Date().toISOString(),
              }
            : audit,
        );
      });
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: AUDIT_QUERY_KEY });
    },
  });
};
