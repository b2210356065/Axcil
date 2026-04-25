import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:file_picker/file_picker.dart';
import 'package:intl/intl.dart';
import '../providers/history_provider.dart';
import '../utils/theme.dart';

class HistoryPage extends ConsumerWidget {
  const HistoryPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final historyAsync = ref.watch(historyNotifierProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('History'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => ref.read(historyNotifierProvider.notifier).loadHistory(),
          ),
        ],
      ),
      body: historyAsync.when(
        data: (history) {
          if (history.isEmpty) {
            return const Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.history, size: 64, color: AppTheme.textSecondary),
                  SizedBox(height: 16),
                  Text(
                    'No files yet',
                    style: TextStyle(fontSize: 18, color: AppTheme.textSecondary),
                  ),
                ],
              ),
            );
          }

          return ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: history.length,
            itemBuilder: (context, index) {
              final item = history[index];
              final dateFormat = DateFormat('MMM dd, yyyy HH:mm');

              return Card(
                margin: const EdgeInsets.only(bottom: 12),
                child: ListTile(
                  leading: Container(
                    width: 40,
                    height: 40,
                    decoration: BoxDecoration(
                      color: AppTheme.accent.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: const Icon(
                      Icons.insert_drive_file,
                      color: AppTheme.accent,
                    ),
                  ),
                  title: Text(item.functionalityName),
                  subtitle: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(item.fileName),
                      Text(
                        '${(item.fileSize / 1024).toStringAsFixed(1)} KB • ${dateFormat.format(item.createdAt)}',
                        style: const TextStyle(fontSize: 12),
                      ),
                    ],
                  ),
                  isThreeLine: true,
                  trailing: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      IconButton(
                        icon: const Icon(Icons.download),
                        onPressed: () => _downloadFile(context, ref, item.id, item.fileName),
                      ),
                      IconButton(
                        icon: const Icon(Icons.delete, color: AppTheme.error),
                        onPressed: () => _deleteFile(context, ref, item.id, item.fileName),
                      ),
                    ],
                  ),
                ),
              );
            },
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => Center(child: Text('Error: $error')),
      ),
    );
  }

  Future<void> _downloadFile(
    BuildContext context,
    WidgetRef ref,
    int historyId,
    String fileName,
  ) async {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Download feature not yet implemented in backend'),
        backgroundColor: AppTheme.warning,
      ),
    );
  }

  void _deleteFile(BuildContext context, WidgetRef ref, int historyId, String fileName) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Delete File'),
        content: Text('Are you sure you want to delete $fileName?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: AppTheme.error),
            onPressed: () {
              ref.read(historyNotifierProvider.notifier).deleteFile(historyId);
              Navigator.pop(context);
            },
            child: const Text('Delete'),
          ),
        ],
      ),
    );
  }
}
