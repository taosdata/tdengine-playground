<template>
  <div id="common-layout">
    <el-container>
      <el-header id="header">
        <a href="https://www.taosdata.com/" title="TDengine | 涛思数据" rel="home">
          <img src="https://docs.taosdata.com/img/site-logo.png">
        </a>
      </el-header>
      <el-container>
        <el-aside width="20vw">
          <div class="card-block" style="margin-left: 3vw;height: 85vh;margin-top: 20px">
            <el-tree :data="preset_sql" @node-click="handleNodeClick" :default-expand-all="true"/>
          </div>
        </el-aside>
        <el-container style="width: 80vw">
          <el-main>
            <div id="sql-editor" class="card-block"></div>
            <el-row>
              <el-col :span="16">
                <el-radio-group v-model="show_mode" class="grid-content" @change="chooseMode">
                  <el-radio-button label="table">
                    <el-icon class="icon-button">
                      <Grid/>
                    </el-icon>
                  </el-radio-button>
                  <el-radio-button label="chart">
                    <el-badge value="show" class="item" type="primary" :hidden="!(checked_columns.length!=1)">
                      <el-icon class="icon-button">
                        <TrendCharts/>
                      </el-icon>
                    </el-badge>

                  </el-radio-button>
                </el-radio-group>
              </el-col>
              <el-col :span="4">
              </el-col>
              <el-col :span="4">
                <div class="grid-content">
                  <el-button size="large" @click="submit_sql" class="td-button">Submit</el-button>
                </div>
              </el-col>
            </el-row>
            <div class="card-block">
              <div id="res-table" v-show="show_mode==='table'">
                <el-auto-resizer>
                  <template #default="{ height, width }">
                    <el-checkbox-group v-model="checked_columns" :min="1" :max="3">
                      <el-table-v2
                          :columns="table_columns"
                          :data="table_data"
                          :width="width"
                          :height="height"
                          :cache="10"
                          :fixed="false"
                          row-class="table_inner"
                      >
                      </el-table-v2>
                    </el-checkbox-group>
                  </template>
                </el-auto-resizer>
              </div>
              <div id="res-chart" v-show="show_mode==='chart'"></div>
              <div id="res-error" v-show="show_mode==='error'">
                <el-result
                    icon="error"
                    title="SQL Error"
                    :sub-title="error_msg"
                    style="margin-top: 10vh"
                ></el-result>
              </div>
            </div>
          </el-main>
          <el-footer>
          </el-footer>
        </el-container>
      </el-container>
    </el-container>
  </div>
</template>

<script lang="tsx" setup>
import * as monaco from 'monaco-editor'
import {onBeforeMount, onMounted, onUnmounted, ref, toRaw} from "vue";
import axios from 'axios'
import * as echarts from "echarts";
import type {HeaderCellSlotProps} from 'element-plus'

// axios.defaults.headers['Authorization'] = 'Basic cm9vdDp0YW9zZGF0YQ=='

let editor: monaco.editor.IStandaloneCodeEditor | null = null//sql编辑器
let chart: echarts.ECharts | null = null;//图表
const show_mode = ref('table')//展示模式
let orgin_data: any = []//原始数据
let table_columns = ref([])//表格列
let table_data = ref([])//表格数据
let chart_data: any[] = []//图表数据
let checked_columns = ref(['ts'])//选中的列
let error_msg = ref('')//错误信息
let authorization = 'Basic cm9vdDp0YW9zZGF0YQ=='//认证信息

interface Tree {
  label: string
  children?: Tree[]
  sql?: string
}

type HeaderSlotProps = {
  cells: VNode[]
  columns: Column<any>[]
  headerIndex: number
}
type HeaderRenderProps<T> = {
  column: Column<T>
  columns: Column<T>[]
  columnIndex: number
  headerIndex: number
}
const headerSlot = ({cells, columns, headerIndex}: HeaderSlotProps) => {
  return cells.map((cell, cellIndex) => {
    const column = columns[cellIndex]
    if (column.type === 'selection') {
      return (
          <el-checkbox
              v-model={column.selectable}
              onChange={() => {
                column.selectable = !column.selectable
              }}
          />
      )
    }
    return cell
  })
}
const preset_sql: Tree[] = [{
  label: 'Sofia weather sensor dataset',
  children: [
    {
      label: 'Query temperature and humidity',
      sql: `SELECT ts,TBNAME,humidity,temperature FROM weather.sensor LIMIT 10000;`
    },
    {
      label: 'Tag-Partitioned Queries',
      sql: `SELECT _wstart,max(temperature),min(temperature),lon,lat from weather.sensor
  PARTITION BY lat,lon
  INTERVAL(6h);`
    },
    {
      label: 'Windowed Queries',
      sql: `SELECT _wstart,AVG(temperature), MAX(temperature), APERCENTILE(temperature, 50) FROM weather.sensor
  WHERE ts>='2017-07-01 00:02:09.000' and ts<='2017-07-13 00:48:39.000'
  INTERVAL(10m)
  FILL(PREV);`
    }
  ],
}, {
  label: 'Wrocław public transport',
  children: [
    {
      label: 'Query public transport',
      sql: `SELECT * FROM transport.gps LIMIT 10000;`,
    }, {
      label: 'Query No. 115 bus',
      sql: `SELECT * FROM transport.gps where line_number=115 LIMIT 10000;`,
    }]
}]
onUnmounted(() => {
  chart.dispose;
  editor.dispose();
});

function initEditor() {
  // 初始化编辑器，确保dom已经渲染
  monaco.editor.defineTheme('my-theme', {
    base: 'vs',
    inherit: true,
    rules: [],
    colors: {
      'editor.background': '#ffffff',
      'editor.lineHighlightBorder': '#cccccc'
    }
  });
  monaco.editor.setTheme('my-theme');
  editor = monaco.editor.create(document.getElementById('sql-editor'), {
    value: 'select * from weather.sensor limit 100;', //编辑器初始显示文字
    language: 'sql', //此处使用的python，其他语言支持自行查阅demo
    theme: 'my-theme', //官方自带三种主题vs, hc-black, or vs-dark
    selectOnLineNumbers: true,//显示行号
    roundedSelection: false,
    readOnly: false, // 只读
    cursorStyle: 'line', //光标样式
    automaticLayout: true, //自动布局
    glyphMargin: true, //字形边缘
    useTabStops: false,
    fontSize: 15, //字体大小
    autoIndent: true, //自动布局
    quickSuggestionsDelay: 100, //代码提示延时,
    minimap: {
      enabled: false
    },
  });
  monaco.editor.defineTheme('mytheme', {
    base: 'vs',
    inherit: false,
    rules: [
      {token: 'source.myLang', foreground: '606266'},
      {background: 'DC143C'}
    ],
    colors: {
      'editor.background': '#8fbda8',
      'editor.lineHighlightBorder': '#cccccc'
    }
  });
  // 监听值的变化
  // editor.value.onDidChangeModelContent((val) => {
  //   // console.log(val.changes[0].text)
  // })
}

const initChart = () => {
  chart = echarts.init(document.getElementById('res-chart'));
}
const handleNodeClick = (data: Tree) => {
  if (data.sql) {
    console.log(toRaw(data.sql))
    editor.setValue(toRaw(data.sql))
  }
}
onMounted(() => {
  initEditor()
  initChart()
  // const columns = generateColumns(['id', 'name', 'age', 'address', 'date'])
  // const data = generateData(columns, ['id', 'name', 'age', 'address', 'date'])
  // console.log(data)
})


const generateColumns = (columns: string[]) =>
    Array.from(columns).map((column) => ({
      key: column,
      dataKey: column,
      title: column,
      // width: 150,
      minWidth: '160px',
      maxWidth: '250px',
      selectable: false,
      align: 'center',

    }))

const generate_table_data = (
    columns: ReturnType<typeof generateColumns>,
    data: []
) =>
    Array.from(data).map((data_line: []) => {
      return columns.reduce(
          (rowData, column, columnIndex) => {
            rowData[column.dataKey] = data_line[columnIndex]
            return rowData
          },
          {
            id: data_line[0],
            parentId: null,
          }
      )
    })

const generate_chart_data = (
    data: [],
    chart_data_index: []
) => {
  return [Array.from(data).map(item => item[0]), Array.from(data).map(item => item[chart_data_index[1]]), Array.from(data).map(item => item[chart_data_index[2]])]
}

const chooseMode = (mode: string) => {
  if (mode === 'chart') {
    let chart_data_index = checked_columns.value.map(item => {
      return orgin_data.head.indexOf(item)
    })
    console.log(chart_data_index)
    chart_data = generate_chart_data(orgin_data.data, chart_data_index)

    // 指定图表的配置项和数据
    let option = {
      title: {
        text: ''
      },
      // visualMap: [
      //   {
      //     show: false,
      //     type: 'continuous',
      //     seriesIndex: 0,
      //     min: 20,
      //     max: 25
      //   },
      //   {
      //     show: false,
      //     type: 'continuous',
      //     seriesIndex: 1,
      //     min: 45,
      //     max: 70
      //   }
      // ],
      tooltip: {
        trigger: 'axis'
      },
      legend: {
        data: [checked_columns.value[1], checked_columns.value[2]],
        padding: [15, 5, 5, 5]

      },
      grid: {
        // left: '3%',
        // right: '3%',
        // bottom: '-10%',
        // top:'-10%',
        // containLabel: true
      },
      toolbox: {},
      dataZoom: [
        {type: 'slider', start: 45, end: 47},
        {type: 'inside', start: 45, end: 47}
      ],
      xAxis: {
        type: 'category',
        data: chart_data[0]
      },
      yAxis: [
        {
          name: checked_columns.value[1],
          type: 'value',
          min: function (value: { min: number; }) {
            return (value.min - 10).toFixed(2);
          }
        },
        {
          name: checked_columns.value[2],
          type: 'value',
          min: function (value: { min: number; }) {
            return (value.min - 10).toFixed(2);
          }
        }
      ],
      series: [
        {
          name: checked_columns.value[1],
          type: 'line',
          data: chart_data[1],
          showSymbol: false,
          smooth: true,
          yAxisIndex: 0,

        },
        {
          name: checked_columns.value[2],
          type: 'line',
          data: chart_data[2],
          showSymbol: false,
          yAxisIndex: 1,
          smooth: true
        }
      ]
    };
    // 使用刚指定的配置项和数据显示图表。
    chart.setOption(option);
  }
}
const submit_sql = () => {
  let sql = editor.getValue()
  table_data.value = []

  axios.post('http://127.0.0.1:6041/rest/sql', sql, {
    headers: {
      'authorization': authorization,
      'Content-Type': 'text/plain'
    }
  }).then(res => {
    checked_columns.value = ['ts']
    if (res.data.code == 0) {//兼容TD3
      res.data.head = res.data.column_meta.map(item => item[0])//兼容TD3
      console.log(res.data)
      let temp = generateColumns(res.data.head)
      console.log(temp)
      temp[0] = {
        key: 'ts',
        dataKey: 'ts',
        title: 'timestamp',
        minWidth: '180px',
        maxWidth: '250px',
        align: 'center',
      }
      temp.slice(1).forEach((column: any) => {
        column.headerCellRenderer = (props: HeaderCellSlotProps) => {
          return (
              <><span>{props.column.title}</span>
                <el-checkbox style="margin-left: 0.8vw"
                    // v-model={column.selectable}
                             key={props.column.dataKey}
                             label={props.column.dataKey}
                             onChange={() => {
                               column.selectable = !column.selectable;
                             }}> </el-checkbox>
              </>
          )
        }
      })
      temp[0].headerCellRenderer = (props: HeaderCellSlotProps) => {
        let true_flag = true
        return (
            <>
              <span>{props.column.title}</span>
              <el-checkbox style="margin-left: 1vw" key={'ts'}
                           label={'ts'} disabled> </el-checkbox>
            </>
        )
      }
      table_columns.value = temp
      table_data.value = generate_table_data(toRaw(table_columns.value), res.data.data)
      orgin_data = res.data
      show_mode.value = 'table'
    } else {
      error_msg.value = res.data.desc
      show_mode.value = 'error'
    }

  })
}

</script>


<style scoped>
#header {
  background-color: cornflowerblue;
  align-items: center;
  display: flex;
}

#header img {
  width: 200px;
  vertical-align: middle;
  height: auto;
  max-width: 100%;
  margin-left: 2.5vw;
}

.el-checkbox-group {
  font-size: inherit !important;
  line-height: inherit !important;
}

.el-main {
  padding-bottom: 0 !important;
}

#common-layout {
  height: 100vh;
  /*width: 100vw;*/
  /*overflow: hidden;*/
  /*margin-right: 2vw;*/
}


.card-block {
  box-shadow: -2px 0 8px rgb(0 0 0 / 2%);
  border-radius: 10px;
  background-color: white;
  padding: 5px;
}

.icon-button {
  font-size: 20px;
}

#res-table {
  height: 55vh;
}

#res-chart {
  height: 55vh;
  width: 70vw;
  /*margin: auto;*/
  /*padding: 0.5vh 2vw;*/
}

#res-error {
  height: 55vh;
  overflow: hidden;
}

#sql-editor {
  height: 16vh;
}

.grid-content {
  margin: 10px 2px;
}

.td-button {
  float: right;
}

.monaco-editor .no-user-select .showUnused .showDeprecated .vs {
  border-radius: 10px !important;
}

.monaco-editor .overflow-guard {
  border-radius: 10px !important;
}

.table_inner {
  overflow: scroll !important;
}


</style>

