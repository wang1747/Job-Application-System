import { type FC } from "react";
import type { Application, ApplicationStatus } from "../types";
import { STATUS_LABELS, STATUS_ORDER } from "../constants/application";

interface KanbanBoardProps {
  items: Application[];
  onStatusChange: (app: Application, status: ApplicationStatus) => void;
  onEdit: (app: Application) => void;
  onDelete: (app: Application) => void;
}

const KanbanBoard: FC<KanbanBoardProps> = ({ items, onStatusChange, onEdit, onDelete }) => {
  const grouped = STATUS_ORDER.reduce((acc, status) => {
    acc[status] = items.filter((item) => item.status === status);
    return acc;
  }, {} as Record<string, Application[]>);

  return (
    <div className="flex gap-3 overflow-x-auto pb-2 min-h-[400px]">
      {STATUS_ORDER.map((status) => (
        <div key={status} className="min-w-[190px] flex-1">
          <h3 className="text-[13px] text-gray-600 m-0 mb-2 px-3 py-2 bg-gray-200 rounded text-center">
            {STATUS_LABELS[status]} ({grouped[status]?.length || 0})
          </h3>
          <div className="flex flex-col gap-2">
            {(grouped[status] || []).map((app) => (
              <div key={app.id} className="bg-white border border-gray-200 rounded-lg p-3 shadow-sm">
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <div className="text-sm font-medium truncate">{app.company}</div>
                    <div className="text-xs text-gray-500 truncate">{app.position}</div>
                  </div>
                  <button
                    onClick={() => onDelete(app)}
                    className="text-xs text-gray-400 hover:text-red-600 flex-shrink-0"
                    aria-label={`删除 ${app.company}`}
                  >
                    删除
                  </button>
                </div>
                {app.next_action && (
                  <div className="mt-2 text-xs text-gray-600 truncate">{app.next_action}</div>
                )}
                {app.next_action_date && (
                  <div className="text-xs text-gray-400">{app.next_action_date}</div>
                )}
                <div className="mt-3">
                  <select
                    value={app.status}
                    onChange={(e) => onStatusChange(app, e.target.value as ApplicationStatus)}
                    className="w-full text-xs border border-gray-300 rounded px-1.5 py-1 bg-white"
                    aria-label={`${app.company} 状态`}
                  >
                    {STATUS_ORDER.map((s) => (
                      <option key={s} value={s}>{STATUS_LABELS[s]}</option>
                    ))}
                  </select>
                </div>
                <button
                  onClick={() => onEdit(app)}
                  className="mt-2 w-full text-xs px-2 py-1.5 rounded border border-gray-300 text-gray-600 hover:bg-gray-50"
                >
                  编辑
                </button>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};

export default KanbanBoard;
