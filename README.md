# Choose Clothing

最高気温と最低気温から、その日の服装を5段階で選び、毎朝スマートフォンに通知できる小さなアプリです。

## 服装ルール

1. 暑い日: `1 6`
2. 少し暑い日: `1 2`
3. ふつうの日: `1 2 3`
4. 少し寒い日: `1 2 3 4`
5. 寒い日: `1 2 3 5`

アイテムの意味:

- `1`: 肌着
- `2`: 綿の長袖
- `3`: ポリエステルの長袖
- `4`: 薄いコート
- `5`: 分厚いコート
- `6`: 半袖の服

## 使い方

手動で気温を渡す:

```bash
python3 clothing_app.py --max-temp 24 --min-temp 16
```

天気APIから取得する:

```bash
python3 clothing_app.py --latitude 35.6762 --longitude 139.6503
```

macOS通知も出す:

```bash
python3 clothing_app.py --latitude 35.6762 --longitude 139.6503 --notify
```

`ntfy` に通知を送る:

```bash
NTFY_TOPIC=your-secret-topic \
python3 clothing_app.py --latitude 35.6762 --longitude 139.6503
```

ローカルのランナーでも `NTFY_TOPIC` を渡せます:

```bash
LATITUDE=35.6762 LONGITUDE=139.6503 NTFY_TOPIC=your-secret-topic ./run_daily_notification.sh
```

## テスト

```bash
python3 -m unittest
```

## 毎朝の自動実行

### おすすめ: GitHub Actions + ntfy

Mac を起動していなくても動かしたい場合は、GitHub Actions で毎朝実行して、`ntfy` でスマートフォンに通知する構成が一番軽いです。

1. スマホに `ntfy` アプリを入れる
2. 推測されにくい長い topic を決めて、その topic を購読する
3. GitHub リポジトリの `Settings > Secrets and variables > Actions` に次の Repository secrets を登録する

- `LATITUDE`: 例 `35.6762`
- `LONGITUDE`: 例 `139.6503`
- `NTFY_TOPIC`: 長いランダム文字列の topic
- `NTFY_SERVER`: 任意。通常は secret を作らず未設定のままでよく、既定値は `https://ntfy.sh`

ワークフローは [daily-notify.yml](/Users/kkawamura/myroot/hobby/choose-clothing/.github/workflows/daily-notify.yml) に入っています。`cron: "0 22 * * *"` は JST の毎朝 7:00 です。

手動実行したい場合は GitHub Actions の `workflow_dispatch` も使えます。

まれに天気APIへの通信で一時的なSSLエラーが出ることがあるため、アプリ側で短いリトライを入れています。

### Mac ローカルでの自動実行

`launchd/com.chooseclothing.daily.plist` を `~/Library/LaunchAgents/` にコピーして読み込むと、Mac起動中に毎朝7:00に通知できます。

```bash
cp launchd/com.chooseclothing.daily.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.chooseclothing.daily.plist
```

緯度経度は `launchd/com.chooseclothing.daily.plist` の `EnvironmentVariables` で変更してください。

## 判定方法

最高気温を 60%、最低気温を 40% として重み付きスコアを作り、次のしきい値で5段階に分けています。

- 27以上: `1 6`
- 21以上: `1 2`
- 15以上: `1 2 3`
- 10以上: `1 2 3 4`
- 10未満: `1 2 3 5`

しきい値はあとで簡単に調整できます。
