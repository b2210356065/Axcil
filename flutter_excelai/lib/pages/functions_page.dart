import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/functionality_provider.dart';
import '../utils/theme.dart';

class FunctionsPage extends ConsumerWidget {
  const FunctionsPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final functionsAsync = ref.watch(functionalityNotifierProvider(1)); // TODO: Dynamic business ID

    return Scaffold(
      appBar: AppBar(
        title: const Text('Functions'),
        actions: [
          IconButton(
            icon: const Icon(Icons.add),
            onPressed: () => _showAddDialog(context, ref),
          ),
        ],
      ),
      body: functionsAsync.when(
        data: (functions) {
          if (functions.isEmpty) {
            return const Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.functions, size: 64, color: AppTheme.textSecondary),
                  SizedBox(height: 16),
                  Text(
                    'No functions yet',
                    style: TextStyle(fontSize: 18, color: AppTheme.textSecondary),
                  ),
                ],
              ),
            );
          }

          return ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: functions.length,
            itemBuilder: (context, index) {
              final func = functions[index];
              return Card(
                margin: const EdgeInsets.only(bottom: 12),
                child: ListTile(
                  leading: Container(
                    width: 40,
                    height: 40,
                    decoration: BoxDecoration(
                      color: AppTheme.primary.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: const Icon(Icons.functions, color: AppTheme.primary),
                  ),
                  title: Text(func.name),
                  subtitle: Text(func.description),
                  trailing: PopupMenuButton(
                    itemBuilder: (context) => [
                      const PopupMenuItem(
                        value: 'edit',
                        child: Text('Edit'),
                      ),
                      const PopupMenuItem(
                        value: 'enrich',
                        child: Text('Enrich'),
                      ),
                      const PopupMenuItem(
                        value: 'delete',
                        child: Text('Delete'),
                      ),
                    ],
                    onSelected: (value) {
                      if (value == 'delete') {
                        ref
                            .read(functionalityNotifierProvider(1).notifier)
                            .deleteFunctionality(func.id);
                      } else if (value == 'enrich') {
                        ref
                            .read(functionalityNotifierProvider(1).notifier)
                            .enrichFunctionality(func.id);
                      }
                    },
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

  void _showAddDialog(BuildContext context, WidgetRef ref) {
    final nameController = TextEditingController();
    final descController = TextEditingController();

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Add Function'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: nameController,
              decoration: const InputDecoration(labelText: 'Name'),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: descController,
              decoration: const InputDecoration(labelText: 'Description'),
              maxLines: 3,
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () {
              ref.read(functionalityNotifierProvider(1).notifier).createFunctionality(
                    name: nameController.text,
                    description: descController.text,
                  );
              Navigator.pop(context);
            },
            child: const Text('Add'),
          ),
        ],
      ),
    );
  }
}
