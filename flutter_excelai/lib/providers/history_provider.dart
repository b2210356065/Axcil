import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/tool_result.dart';
import '../services/history_service.dart';

final historyServiceProvider = Provider((ref) => HistoryService());

final historyListProvider = FutureProvider<List<ToolResult>>((ref) async {
  final service = ref.watch(historyServiceProvider);
  return await service.getHistory();
});

final historyNotifierProvider =
    StateNotifierProvider<HistoryNotifier, AsyncValue<List<ToolResult>>>((ref) {
  return HistoryNotifier(ref.watch(historyServiceProvider));
});

class HistoryNotifier extends StateNotifier<AsyncValue<List<ToolResult>>> {
  final HistoryService _service;

  HistoryNotifier(this._service) : super(const AsyncValue.loading()) {
    loadHistory();
  }

  Future<void> loadHistory() async {
    state = const AsyncValue.loading();
    try {
      final history = await _service.getHistory();
      state = AsyncValue.data(history);
    } catch (e, stack) {
      state = AsyncValue.error(e, stack);
    }
  }

  Future<void> downloadFile(int historyId, String savePath) async {
    try {
      await _service.downloadFile(historyId, savePath);
    } catch (e) {
      // Error handling
    }
  }

  Future<void> deleteFile(int historyId) async {
    try {
      await _service.deleteFile(historyId);
      await loadHistory();
    } catch (e) {
      // Error handling
    }
  }
}
