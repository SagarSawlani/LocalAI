import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'dart:async';

class SearchScreen extends StatefulWidget {
  const SearchScreen({super.key});

  @override
  State<SearchScreen> createState() => _SearchScreenState();
}

class _SearchScreenState extends State<SearchScreen> {
  final TextEditingController _controller = TextEditingController();
  String _answer = "";
  bool _loading = false;
  StreamSubscription? _sub;

  static const String baseUrl = "http://127.0.0.1:8000";

  Future<void> _search() async {
    final query = _controller.text.trim();
    if (query.isEmpty) return;

    setState(() {
      _answer = "";
      _loading = true;
    });

    try {
      final client = http.Client();
      final request = http.Request(
        "GET",
        Uri.parse("$baseUrl/docs/ask/stream?query=${Uri.encodeQueryComponent(query)}"),
      );
      final response = await client.send(request);

      _sub = response.stream
          .transform(utf8.decoder)
          .listen(
        (chunk) {
          setState(() {
            _answer += chunk;
          });
        },
        onDone: () {
          setState(() => _loading = false);
          client.close();
        },
        onError: (e) {
          setState(() {
            _answer += "\n[Error: $e]";
            _loading = false;
          });
          client.close();
        },
      );
    } catch (e) {
      setState(() {
        _answer = "Error: $e";
        _loading = false;
      });
    }
  }

  @override
  void dispose() {
    _sub?.cancel();
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Search Documents")),
      body: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _controller,
                    decoration: const InputDecoration(
                      hintText: "Ask about your documents...",
                      border: OutlineInputBorder(),
                    ),
                    onSubmitted: (_) => _search(),
                  ),
                ),
                const SizedBox(width: 8),
                IconButton(
                  icon: const Icon(Icons.search),
                  onPressed: _search,
                ),
              ],
            ),
            const SizedBox(height: 12),
            if (_loading && _answer.isEmpty)
              const Padding(
                padding: EdgeInsets.all(16),
                child: CircularProgressIndicator(),
              ),
            Expanded(
              child: SingleChildScrollView(
                child: Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.grey[100],
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(_answer),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
